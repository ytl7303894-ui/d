<?php
// ZRY X PREMIUM HOSTING - Reborn Script
// File Manager with Upload, Editor, Preview

session_start();

// Configuration
$BASE_DIR = __DIR__ . '/files'; // Sab files yahan save hongi
$BASE_URL = 'files'; // URL path

// Base directory create karo agar exist nahi karta
if (!file_exists($BASE_DIR)) {
    mkdir($BASE_DIR, 0777, true);
}

// Current path handle karo
$current_path = isset($_GET['path']) ? $_GET['path'] : '';
$current_dir = $BASE_DIR . ($current_path ? '/' . $current_path : '');
$current_dir = realpath($current_dir);

// Security: Check karo ki path base directory ke andar hai
if (strpos($current_dir, realpath($BASE_DIR)) !== 0) {
    $current_dir = realpath($BASE_DIR);
    $current_path = '';
}

// File upload handle karo
$upload_message = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['file'])) {
    $target_dir = $current_dir . '/';
    $target_file = $target_dir . basename($_FILES['file']['name']);
    
    if (move_uploaded_file($_FILES['file']['tmp_name'], $target_file)) {
        $upload_message = '<div style="color: green; padding: 10px;">✓ File uploaded: ' . htmlspecialchars($_FILES['file']['name']) . '</div>';
    } else {
        $upload_message = '<div style="color: red; padding: 10px;">✗ Upload failed</div>';
    }
}

// File delete handle karo
if (isset($_GET['delete']) && !empty($_GET['delete'])) {
    $file_to_delete = $current_dir . '/' . basename($_GET['delete']);
    if (file_exists($file_to_delete) && is_file($file_to_delete)) {
        unlink($file_to_delete);
    }
    header('Location: ?path=' . urlencode($current_path));
    exit;
}

// File save handle karo (editor se)
if (isset($_POST['save_file']) && isset($_POST['file_content']) && isset($_POST['file_path'])) {
    $file_path = $BASE_DIR . '/' . $_POST['file_path'];
    if (file_exists($file_path) && is_file($file_path)) {
        file_put_contents($file_path, $_POST['file_content']);
        header('Location: ?path=' . urlencode(dirname($_POST['file_path'])) . '&edited=1');
        exit;
    }
}

// Get files list
$items = [];
if (is_dir($current_dir)) {
    $files = scandir($current_dir);
    foreach ($files as $file) {
        if ($file != '.' && $file != '..') {
            $file_path = $current_dir . '/' . $file;
            $items[] = [
                'name' => $file,
                'type' => is_dir($file_path) ? 'folder' : 'file',
                'size' => is_file($file_path) ? formatSize(filesize($file_path)) : '-',
                'modified' => date('Y-m-d H:i:s', filemtime($file_path)),
                'path' => ($current_path ? $current_path . '/' : '') . $file
            ];
        }
    }
}

// Helper function: Format file size
function formatSize($bytes) {
    if ($bytes >= 1073741824) return number_format($bytes / 1073741824, 2) . ' GB';
    if ($bytes >= 1048576) return number_format($bytes / 1048576, 2) . ' MB';
    if ($bytes >= 1024) return number_format($bytes / 1024, 2) . ' KB';
    return $bytes . ' B';
}

// Calculate total storage
function getTotalSize($dir) {
    $size = 0;
    if (is_dir($dir)) {
        foreach (scandir($dir) as $file) {
            if ($file != '.' && $file != '..') {
                $path = $dir . '/' . $file;
                if (is_file($path)) $size += filesize($path);
                if (is_dir($path)) $size += getTotalSize($path);
            }
        }
    }
    return $size;
}
$total_storage = getTotalSize($BASE_DIR);
$site_count = count(glob($BASE_DIR . '/*', GLOB_ONLYDIR));
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ ZRY X PREMIUM HOSTING</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif; }
        body { background: linear-gradient(145deg, #0a0b0e 0%, #14161b 100%); color: #e4e6eb; min-height: 100vh; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        
        /* Header */
        .header { background: rgba(26, 30, 36, 0.95); backdrop-filter: blur(10px); border-radius: 24px; padding: 24px 32px; margin-bottom: 24px; border: 1px solid rgba(75, 130, 245, 0.2); box-shadow: 0 15px 35px rgba(0,0,0,0.5); }
        .logo { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
        .logo h1 { font-size: 2.2rem; font-weight: 700; background: linear-gradient(135deg, #4b82f5, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.5px; }
        .badges { display: flex; gap: 15px; flex-wrap: wrap; }
        .badge { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 100px; padding: 8px 18px; font-size: 0.9rem; font-weight: 500; }
        .badge i { margin-right: 8px; opacity: 0.8; }
        .user-id { background: #1e1f2a; padding: 10px 20px; border-radius: 12px; font-family: monospace; border-left: 4px solid #4b82f5; margin-top: 15px; color: #a0a8c0; }
        
        /* Cards Grid */
        .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: rgba(20, 24, 30, 0.8); backdrop-filter: blur(8px); border: 1px solid rgba(75, 130, 245, 0.15); border-radius: 28px; padding: 24px; transition: all 0.3s ease; box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5); }
        .card:hover { transform: translateY(-4px); border-color: rgba(75, 130, 245, 0.4); box-shadow: 0 20px 40px -10px #4b82f540; }
        .card-icon { font-size: 2.2rem; margin-bottom: 18px; filter: drop-shadow(0 0 15px #4b82f580); }
        .card h3 { font-size: 1.3rem; font-weight: 600; margin-bottom: 12px; color: white; }
        .card .url { background: #0d0f14; padding: 10px 14px; border-radius: 14px; font-family: monospace; margin: 15px 0; border: 1px solid #2a2e3a; font-size: 0.9rem; }
        
        /* Upload Area */
        .upload-area { border: 2px dashed #3a4050; border-radius: 20px; padding: 30px; text-align: center; background: #0f1219; margin: 20px 0; transition: 0.2s; cursor: pointer; }
        .upload-area:hover { border-color: #4b82f5; background: #131722; }
        .upload-btn { background: linear-gradient(135deg, #4b82f5, #6d5df5); border: none; color: white; padding: 14px 32px; border-radius: 40px; font-weight: 600; font-size: 1.1rem; cursor: pointer; box-shadow: 0 10px 20px -5px #4b82f580; transition: 0.2s; }
        .upload-btn:hover { transform: scale(1.02); }
        
        /* File Manager Table */
        .file-manager { background: rgba(20, 24, 30, 0.8); border-radius: 28px; padding: 24px; border: 1px solid #2a2e3a; margin-top: 25px; }
        .table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 15px; }
        .path-nav { background: #1a1d26; padding: 10px 16px; border-radius: 40px; font-size: 0.95rem; }
        .path-nav a { color: #8b9bff; text-decoration: none; margin: 0 5px; }
        .path-nav a:hover { text-decoration: underline; }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; padding: 15px 10px; color: #8e9bb5; font-weight: 500; border-bottom: 2px solid #2a2e3a; }
        td { padding: 14px 10px; border-bottom: 1px solid #252a34; }
        tr:hover td { background: #1f232e; }
        .file-actions a { color: #adb5bd; margin: 0 8px; text-decoration: none; font-size: 1.2rem; transition: 0.2s; display: inline-block; }
        .file-actions a:hover { color: #4b82f5; transform: scale(1.1); }
        .folder-item { color: #ffd966; font-weight: 500; }
        .file-item { color: #b0c4de; }
        
        /* Stats */
        .stats-row { display: flex; gap: 25px; margin: 25px 0; flex-wrap: wrap; }
        .stat-item { background: #1a1e2a; padding: 18px 28px; border-radius: 40px; border-left: 5px solid #4b82f5; }
        .stat-number { font-size: 2rem; font-weight: 700; color: white; }
        
        /* Modal/Editor */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); backdrop-filter: blur(5px); justify-content: center; align-items: center; z-index: 1000; }
        .modal-content { background: #1c2029; border-radius: 32px; width: 90%; max-width: 800px; padding: 30px; border: 1px solid #3a4055; }
        .modal-header { display: flex; justify-content: space-between; margin-bottom: 20px; }
        .close-btn { background: none; border: none; color: #aaa; font-size: 28px; cursor: pointer; }
        textarea { width: 100%; height: 400px; background: #0d0f17; border: 1px solid #2f3545; color: #e0e0e0; border-radius: 16px; padding: 20px; font-family: monospace; resize: vertical; margin: 15px 0; }
        .save-btn { background: #4b82f5; border: none; color: white; padding: 14px 32px; border-radius: 40px; font-weight: bold; cursor: pointer; }
        
        @media (max-width: 700px) { .features-grid { grid-template-columns: 1fr; } .header { padding: 20px; } }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="logo">
                <span style="font-size: 2.5rem;">⚡</span>
                <h1>ZRY X PREMIUM HOSTING</h1>
            </div>
            <div class="badges">
                <span class="badge"><i>📱</i> Mobile Friendly</span>
                <span class="badge"><i>🔒</i> Password Protected</span>
                <span class="badge"><i>📁</i> Your Files Only</span>
            </div>
            <div class="user-id">
                Your User ID: user_<?php echo substr(md5(session_id()), 0, 12); ?>...
            </div>
            <?php echo $upload_message; ?>
        </div>

        <!-- Feature Cards (Exactly like your original) -->
        <div class="features-grid">
            <div class="card">
                <div class="card-icon">📄</div>
                <h3>UPLOAD FILES</h3>
                <form method="post" enctype="multipart/form-data" id="uploadForm">
                    <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                        <p style="margin-bottom: 15px;">⬆️ Click to Upload</p>
                        <p style="color: #8e9bb5; font-size: 0.9rem;">HTML, CSS, JS, ZIP files</p>
                        <input type="file" name="file" id="fileInput" style="display: none;" onchange="document.getElementById('uploadForm').submit()">
                    </div>
                </form>
                <div class="url">URL: view.php?site=my-site</div>
            </div>

            <div class="card">
                <div class="card-icon">💻</div>
                <h3>Code Editor</h3>
                <p style="margin: 15px 0; color: #b0b9d0;">Type code in editor tab to see preview</p>
                <div class="url">Click on any file to edit</div>
            </div>

            <div class="card">
                <div class="card-icon">👁️</div>
                <h3>Live Preview</h3>
                <p style="margin: 15px 0;">View your HTML files live</p>
                <div class="url">URL: view.php?site=my-website</div>
            </div>

            <div class="card">
                <div class="card-icon">📊</div>
                <h3>Analytics</h3>
                <p style="margin: 15px 0;">Select a site to view analytics</p>
                <div class="stats-row" style="margin-top: 20px;">
                    <div class="stat-item"><span class="stat-number"><?php echo $site_count; ?></span> Sites</div>
                    <div class="stat-item"><span class="stat-number"><?php echo formatSize($total_storage); ?></span> Storage</div>
                </div>
            </div>
        </div>

        <!-- File Manager Section -->
        <div class="file-manager">
            <div class="table-header">
                <h2>📁 File Manager</h2>
                <div class="path-nav">
                    <a href="?path=">Root</a> 
                    <?php 
                    if ($current_path) {
                        $parts = explode('/', $current_path);
                        $cumulative = '';
                        foreach ($parts as $part) {
                            $cumulative .= ($cumulative ? '/' : '') . $part;
                            echo '/ <a href="?path=' . urlencode($cumulative) . '">' . htmlspecialchars($part) . '</a> ';
                        }
                    }
                    ?>
                </div>
            </div>

            <?php if (empty($items)): ?>
                <div style="text-align: center; padding: 50px 20px; background: #161a24; border-radius: 24px;">
                    <div style="font-size: 3rem; margin-bottom: 20px;">📭</div>
                    <h3>No Websites Yet</h3>
                    <p style="color: #8e9bb5; margin-top: 10px;">Upload your first file to get started!</p>
                </div>
            <?php else: ?>
                <table>
                    <thead>
                        <tr><th>Name</th><th>Size</th><th>Modified</th><th>Actions</th></tr>
                    </thead>
                    <tbody>
                        <?php foreach ($items as $item): ?>
                        <tr>
                            <td>
                                <?php if ($item['type'] == 'folder'): ?>
                                    <span class="folder-item">📁 <a href="?path=<?php echo urlencode($item['path']); ?>" style="color: #ffd966; text-decoration: none;"><?php echo htmlspecialchars($item['name']); ?></a></span>
                                <?php else: ?>
                                    <span class="file-item">📄 <?php echo htmlspecialchars($item['name']); ?></span>
                                <?php endif; ?>
                            </td>
                            <td><?php echo $item['size']; ?></td>
                            <td><?php echo $item['modified']; ?></td>
                            <td class="file-actions">
                                <?php if ($item['type'] == 'file'): ?>
                                    <a href="#" onclick="openEditor('<?php echo htmlspecialchars($item['path']); ?>'); return false;" title="Edit">✏️</a>
                                    <a href="<?php echo $BASE_URL . '/' . htmlspecialchars($item['path']); ?>" target="_blank" title="Preview">👁️</a>
                                    <a href="?delete=<?php echo urlencode(basename($item['path'])); ?>&path=<?php echo urlencode($current_path); ?>" onclick="return confirm('Delete file?')" title="Delete">🗑️</a>
                                <?php else: ?>
                                    <span style="opacity: 0.3;">——</span>
                                <?php endif; ?>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            <?php endif; ?>
        </div>
    </div>

    <!-- Editor Modal -->
    <div id="editorModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>💻 Editing: <span id="editFileName"></span></h2>
                <button class="close-btn" onclick="closeEditor()">&times;</button>
            </div>
            <form method="post" id="editorForm">
                <input type="hidden" name="file_path" id="editFilePath">
                <textarea name="file_content" id="editFileContent" placeholder="Loading file content..."></textarea>
                <button type="submit" name="save_file" class="save-btn">💾 Save Changes</button>
            </form>
        </div>
    </div>

    <script>
        function openEditor(filePath) {
            document.getElementById('editFileName').textContent = filePath;
            document.getElementById('editFilePath').value = filePath;
            
            // Fetch file content via AJAX
            fetch('get-file.php?file=' + encodeURIComponent(filePath))
                .then(response => response.text())
                .then(content => {
                    document.getElementById('editFileContent').value = content;
                })
                .catch(error => {
                    document.getElementById('editFileContent').value = '// Error loading file';
                });
            
            document.getElementById('editorModal').style.display = 'flex';
        }
        
        function closeEditor() {
            document.getElementById('editorModal').style.display = 'none';
        }
        
        window.onclick = function(event) {
            if (event.target == document.getElementById('editorModal')) {
                closeEditor();
            }
        }
    </script>
</body>
</html>
<?php
// Editor ke liye file content lene ka endpoint
if (isset($_GET['file']) && isset($_SERVER['HTTP_X_REQUESTED_WITH']) && $_SERVER['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest') {
    $file = $BASE_DIR . '/' . $_GET['file'];
    if (file_exists($file) && is_file($file)) {
        header('Content-Type: text/plain');
        echo file_get_contents($file);
    }
    exit;
}
?>
