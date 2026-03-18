<?php
header('Content-Type: application/json');

// RC lookup powered by BasicCoders
$rcNumber = isset($_GET['rc']) ? strtoupper(trim($_GET['rc'])) : '';
if (!$rcNumber) {
    echo json_encode(["status" => "error", "message" => "No RC number provided"]);
    exit;
}

$url = "https://vahanx.in/rc-search/" . urlencode($rcNumber);

$headers = [
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
];

$ch = curl_init($url);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER => $headers,
    CURLOPT_TIMEOUT => 10
]);

$html = curl_exec($ch);
if (curl_errno($ch)) {
    echo json_encode(["status" => "error", "message" => "Network error: " . curl_error($ch)]);
    exit;
}
curl_close($ch);

// Parse HTML
libxml_use_internal_errors(true);
$dom = new DOMDocument();
$dom->loadHTML($html);
$xpath = new DOMXPath($dom);

$desiredOrder = [
    "Owner Name", "Father's Name", "Owner Serial No", "Model Name", "Maker Model",
    "Vehicle Class", "Fuel Type", "Fuel Norms", "Registration Date", "Insurance Company",
    "Insurance No", "Insurance Expiry", "Insurance Upto", "Fitness Upto", "Tax Upto",
    "PUC No", "PUC Upto", "Financier Name", "Registered RTO", "Address", "City Name", "Phone"
];

$details = [];

foreach ($desiredOrder as $label) {
    // find span containing label text
    $query = "//span[text()='" . $label . "']/parent::div/p";
    $nodes = $xpath->query($query);
    $value = ($nodes->length > 0) ? trim($nodes->item(0)->textContent) : null;
    if ($value) {
        $details[$label] = $value;
    }
}

if (!empty($details)) {
    echo json_encode([
        "status" => "success",
        "rc_number" => $rcNumber,
        "details" => $details,
        "Join" => "@LegendXTrick"
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
} else {
    echo json_encode([
        "status" => "error",
        "message" => "No details found or invalid RC number.",
        "Join" => "👨@LegendXTrick"
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}
?>
