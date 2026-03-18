<?php
// get-file.php - File content loader for editor
session_start();
$BASE_DIR = __DIR__ . '/files';
$file = isset($_GET['file']) ? $_GET['file'] : '';
$file_path = $BASE_DIR . '/' . $file;

if (file_exists($file_path) && is_file($file_path)) {
    header('Content-Type: text/plain');
    readfile($file_path);
} else {
    http_response_code(404);
    echo 'File not found';
}
?>
