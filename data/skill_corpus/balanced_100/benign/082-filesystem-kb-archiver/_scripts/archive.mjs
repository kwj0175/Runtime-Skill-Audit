#!/usr/bin/env node
/**
 * Knowledge Base Archiver
 * 
 * Usage: node archive.mjs <filepath> [category]
 * 
 * Features:
 * - Auto-classify files by content/filename
 * - Extract full-text index (xlsx/docx/pptx/pdf/txt)
 * - Local storage for < 10MB files
 * - Cloud storage for >= 10MB files (requires configuration)
 * - Generate manifest JSON
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const KB_ROOT = path.resolve(__dirname, '..');
const SIZE_LIMIT = 10 * 1024 * 1024; // 10MB
const INDEX_DIR = path.join(KB_ROOT, '_index');

// ============ CONFIGURATION ============

// Auto-classify rules (keyword -> category)
const CATEGORIES = {
  '工作文件': ['数据', '报表', '统计', '追踪', '明细', '汇总', '门店', '评分', '差评', '推广', '消耗', '投入', '营业'],
  '方案文档': ['方案', '计划', '策略', '执行表', '管理', '动作', '流程', '制度', '规范'],
  '参考资料': ['话术', '模板', '技巧', '申诉', '回访', '指南', '手册', '培训', '教程'],
};

// Valid categories
const VALID_CATEGORIES = [...Object.keys(CATEGORIES), '其他文档'];

// Cloud storage configuration (optional)
// Fill in to enable cloud upload for large files
// Supported: coscmd, aws-cli, ossutil, etc.
const CLOUD_STORAGE = {
  enabled: false,
  // type: 'cos',        // 'cos' | 's3' | 'oss' | 'obs'
  // bucket: '',         // e.g. 'mybucket-1250000000'
  // prefix: 'knowledge-base/',
  // region: '',         // e.g. 'ap-guangzhou'
  // 
  // For COS: use coscmd
  // command: (filepath, remotePath) => `coscmd upload "${filepath}" "${remotePath}"`,
  //
  // For S3: use aws-cli
  // command: (filepath, remotePath) => `aws s3 cp "${filepath}" "s3://${bucket}/${remotePath}"`,
  //
  // For OSS: use ossutil
  // command: (filepath, remotePath) => `ossutil cp "${filepath}" "oss://${bucket}/${remotePath}"`,
};

// Feishu bitable configuration (optional)
// Fill in to enable auto-indexing
const FEISHU_BITABLE = {
  enabled: false,
  // app_token: '',
  // table_id: '',
  // open_id: '',       // Current user's open_id
};

// ============ FUNCTIONS ============

function autoClassify(filename, summary = '') {
  const text = (filename + ' ' + summary).toLowerCase();
  for (const [cat, keywords] of Object.entries(CATEGORIES)) {
    if (keywords.some(k => text.includes(k.toLowerCase()))) {
      return cat;
    }
  }
  return '其他文档';
}

function extractText(filePath, ext) {
  try {
    if (ext === 'xlsx') {
      return extractExcel(filePath);
    } else if (ext === 'docx') {
      return extractDocx(filePath);
    } else if (ext === 'pptx') {
      return extractPptx(filePath);
    } else if (['pdf', 'txt', 'csv', 'md', 'json', 'xml', 'html', 'log'].includes(ext)) {
      try {
        return fs.readFileSync(filePath, 'utf-8');
      } catch {
        return '';
      }
    }
    return `[${ext} format not supported for full-text extraction]`;
  } catch (e) {
    return `[Extraction failed: ${e.message}]`;
  }
}

function extractExcel(filePath) {
  const out = execSync(`python3 -c "
import openpyxl, json
try:
    wb = openpyxl.load_workbook('${filePath}', data_only=True)
    lines = []
    for sheet in wb.sheetnames:
        lines.append(f'Sheet: {sheet}')
        for row in wb[sheet].iter_rows(values_only=True):
            if any(c for c in row if c):
                lines.append(' | '.join(str(c) if c else '' for c in row))
    print(json.dumps('\\n'.join(lines)))
except Exception as e:
    print(json.dumps(f'Error: {str(e)}'))
"`, { encoding: 'utf-8', maxBuffer: 50 * 1024 * 1024 });
  return JSON.parse(out.trim());
}

function extractDocx(filePath) {
  const out = execSync(`python3 -c "
import zipfile, re, json
try:
    with zipfile.ZipFile('${filePath}') as z:
        doc = z.read('word/document.xml').decode('utf-8')
        texts = re.findall(r'<w:t[^>]*>([^<]+)</w:t>', doc)
        print(json.dumps(''.join(texts)))
except Exception as e:
    print(json.dumps(f'Error: {str(e)}'))
"`, { encoding: 'utf-8', maxBuffer: 50 * 1024 * 1024 });
  return JSON.parse(out.trim());
}

function extractPptx(filePath) {
  const out = execSync(`python3 -c "
import zipfile, re, json
try:
    with zipfile.ZipFile('${filePath}') as z:
        slides = sorted([f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')])
        texts = []
        for sf in slides:
            slide = z.read(sf).decode('utf-8')
            texts.extend(re.findall(r'<a:t>([^<]+)</a:t>', slide))
        print(json.dumps('\\n'.join(texts)))
except Exception as e:
    print(json.dumps(f'Error: {str(e)}'))
"`, { encoding: 'utf-8', maxBuffer: 50 * 1024 * 1024 });
  return JSON.parse(out.trim());
}

function generateSummary(filename, text) {
  const clean = text.replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();
  if (clean.length <= 100) return clean || `${filename}`;
  return clean.substring(0, 100) + '...';
}

function uploadToCloud(filePath, remotePath) {
  if (!CLOUD_STORAGE.enabled || !CLOUD_STORAGE.command) {
    console.log('  ☁️  Cloud storage not configured, skipping upload');
    return null;
  }
  try {
    const cmd = CLOUD_STORAGE.command(filePath, remotePath);
    execSync(cmd, { timeout: 120000 });
    return remotePath;
  } catch (e) {
    console.error(`  ❌ Cloud upload failed: ${e.message}`);
    return null;
  }
}

function updateManifest(entry) {
  const manifestPath = path.join(INDEX_DIR, '_manifest.json');
  let manifest = [];
  try {
    manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
  } catch {}
  manifest.push(entry);
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf-8');
}

// ============ MAIN ============

function main() {
  const [,, filePath, manualCategory] = process.argv;

  if (!filePath) {
    console.error('Usage: node archive.mjs <filepath> [category]');
    console.error(`Valid categories: ${VALID_CATEGORIES.join(', ')}`);
    process.exit(1);
  }

  if (!fs.existsSync(filePath)) {
    console.error(`File not found: ${filePath}`);
    process.exit(1);
  }

  // Initialize directories
  for (const cat of VALID_CATEGORIES) {
    const catDir = path.join(KB_ROOT, cat);
    if (!fs.existsSync(catDir)) fs.mkdirSync(catDir, { recursive: true });
  }
  if (!fs.existsSync(INDEX_DIR)) fs.mkdirSync(INDEX_DIR, { recursive: true });

  const filename = path.basename(filePath);
  const stats = fs.statSync(filePath);
  const size = stats.size;
  const ext = filename.split('.').pop().toLowerCase();

  console.log(`📄 Processing: ${filename} (${(size / 1024 / 1024).toFixed(2)}MB)`);

  // Extract text
  const text = extractText(filePath, ext);
  const summary = generateSummary(filename, text);
  const category = manualCategory && VALID_CATEGORIES.includes(manualCategory)
    ? manualCategory
    : autoClassify(filename, summary);

  console.log(`📂 Category: ${category}`);
  console.log(`📝 Summary: ${summary.substring(0, 60)}`);

  let storagePath = '';
  let cosUrl = '';

  if (size < SIZE_LIMIT) {
    // Local storage
    const destDir = path.join(KB_ROOT, category);
    const destPath = path.join(destDir, filename);
    fs.copyFileSync(filePath, destPath);
    storagePath = `${category}/${filename}`;
    console.log(`💾 Local: ${destPath}`);
  } else {
    // Cloud storage
    console.log(`☁️  Uploading to cloud (>10MB)...`);
    const remotePath = `knowledge-base/${category}/${filename}`;
    const result = uploadToCloud(filePath, remotePath);
    storagePath = result ? `cloud://${remotePath}` : '';
    console.log(`☁️  Cloud: ${storagePath}`);
  }

  // Create full-text index
  const idxName = filename.replace(/\.[^.]+$/, '');
  const idxPath = path.join(INDEX_DIR, `${idxName}.txt`);
  const idxContent = [
    `# ${filename}`,
    `Category: ${category}`,
    `Size: ${(size / 1024).toFixed(1)}KB`,
    `Date: ${new Date().toISOString().split('T')[0]}`,
    `Path: ${storagePath}`,
    '---',
    '',
    text,
  ].join('\n');
  fs.writeFileSync(idxPath, idxContent, 'utf-8');
  console.log(`📇 Index: ${idxPath} (${text.length} chars)`);

  // Update manifest
  updateManifest({
    name: filename,
    category,
    size,
    textLength: text.length,
    storagePath,
    indexFile: `${idxName}.txt`,
    summary,
    archivedAt: new Date().toISOString(),
  });

  console.log('\n✅ Archive complete!');
}

main();
