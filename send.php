<?php

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    
    $name = htmlspecialchars(trim($_POST["name"]));
    $email = htmlspecialchars(trim($_POST["email"]));
    $message = htmlspecialchars(trim($_POST["message"]));
    $date = date("Y-m-d H:i:s");

    
    $entry = "----- New Message -----\n";
    $entry .= "Date: $date\n";
    $entry .= "Name: $name\n";
    $entry .= "Email: $email\n";
    $entry .= "Message:\n$message\n\n";


    $file = fopen("messages.txt", "a");
    fwrite($file, $entry);
    fclose($file);

    
    echo "
    <html>
    <head>
        <title>Message Sent</title>
        <style>
          body {font-family: Arial; background:#0a192f; color:#64ffda; text-align:center; padding:60px;}
          a {color:#64ffda; text-decoration:none;}
        </style>
    </head>
    <body>
        <h2>✅ Thank you, $name!</h2>
        <p>Your message has been received successfully.</p>
        <a href='index.html'>← Go Back to Home</a>
    </body>
    </html>
    ";
}
?>
