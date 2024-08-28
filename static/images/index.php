<?php
// Establish a database connection
$servername = "localhost";
$username = "dbadmin";
$password = "/DdhEoI(2C*[SRh7";
$dbname = "darkweb";

$conn = mysqli_connect($servername, $username, $password, $dbname);

// Check connection
if (!$conn) {
    die("Connection failed: " . mysqli_connect_error());
}

// If the user has submitted the sign-in form
if (isset($_POST['submit'])) {
    $username = mysqli_real_escape_string($conn, $_POST['username']);
    $password = mysqli_real_escape_string($conn, $_POST['password']);

    // Query the database to check if the entered username and password are correct
    $sql = "SELECT sno FROM users WHERE username = '$username' AND password = '$password'";
    $result = mysqli_query($conn, $sql);

    if (mysqli_num_rows($result) == 1) {
        // If the query returned one row, the user is authenticated
        session_start();
        $_SESSION['username'] = $username;
        header("Location: welcome.php");
        exit();
    } else {
        // If the query returned zero or multiple rows, the user is not authenticated
        $error = "Invalid username or password";
    }
}

mysqli_close($conn);
?>


<!DOCTYPE html>
<html lang="en" class="a0">
   <head>
      <meta charset="UTF-8" />
      <meta http-equiv="X-UA-Compatible" content="IE=edge" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Sign In | Appline Tailwind App Landing Template</title>
      <link rel="shortcut icon" href="../images/favicon.png" type="image/x-icon" />
      <link rel="stylesheet" href="../css/swiper-bundle.min.css" />
      <link rel="stylesheet" href="../css/animate.css" />
      <link rel="stylesheet" href="../css/glightbox.min.css" />
      <link rel="stylesheet" href="../css/tailwind.css" />
   </head>
   <body class="a1 dark:a2">
      <main>
         <section class="a1t[150px] a1u[110px] lg:a1t[220px]">
            <div class="ab a1v lg:ad[1250px]">
               <div class="wow fadeInUp a1w a7 ad[520px] a14 a1e[#F8FAFB] a3E a1n a19 dark:a1e[#15182A] dark:a1f sm:a3A[50px]" data-wow-delay=".2s">
                  <div class="aF">
                     <center><img src="https://mail.techmedok.com/nl.png" width="20%"></center>
                     <p class="a1J aR a1B">
                        <?php if (isset($error)): ?>
                        <p style="color: red;"><?php echo $error; ?></p>
                      <?php endif; ?>
                     </p>

                  </div>
                  <form method="POST">
                     <div class="a2d">
                        <label for="username" class="a1z[10px] ah a2C aT dark:aV">
                        Username
                        </label>
                        <input type="text" name="uname" required placeholder="Enter your username" class="a7 a1p a3u a8 a1 a1D a1n aR aS a1B a45 focus:a46 focus:a4c dark:aa dark:a2 dark:aV dark:focus:a46" />
                     </div>
                     <div class="a2n">
                        <label for="password" class="a1z[10px] ah a2C aT dark:aV">
                        Password
                        </label>
                        <input type="password" name="password" required placeholder="Enter your password" class="a7 a1p a3u a8 a1 a1D a1n aR aS a1B a45 focus:a46 focus:a4c dark:aa dark:a2 dark:aV dark:focus:a46" />
                     </div>
                     <button type="submit" style="background-color: black;" class="ae a7 ar a1p a1q a49 aR aS aV hover:a1s">
                     Sign In
                     </button>
                  </form>
               </div>
            </div>
         </section>
      </main>
      <a href="javascript:void(0)" class="back-to-top aw a1_ a20 a21 az[999] ak an ao af ar a1p a1q aV a22 a9 a23 hover:a24">
      <span class="a25[6px] a26 a1N aA a27 a28 a29"></span>
      </a>
      <script src="../js/swiper-bundle.min.js"></script>
      <script src="../js/glightbox.min.js"></script>
      <script src="../js/wow.min.js"></script>
      <script src="../js/index.js"></script>
   </body>
</html>