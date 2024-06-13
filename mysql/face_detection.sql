-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jun 13, 2024 at 06:52 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `face_detection`
--

-- --------------------------------------------------------

--
-- Table structure for table `classify_esp32`
--

CREATE TABLE `classify_esp32` (
  `id` int(11) NOT NULL,
  `webcam_token` varchar(10) NOT NULL,
  `mens_detected` int(11) NOT NULL,
  `womens_detected` int(11) NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `classify_media`
--

CREATE TABLE `classify_media` (
  `id` int(11) NOT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp(),
  `filename` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `classify_media`
--

INSERT INTO `classify_media` (`id`, `gender`, `timestamp`, `filename`) VALUES
(1, 'Male', '2024-06-13 04:33:29', '1716828031782.jpeg'),
(2, 'Female', '2024-06-13 04:34:14', '1716827863560.jpeg'),
(3, 'Male', '2024-06-13 04:34:21', '1716828031827.jpg'),
(4, 'Female', '2024-06-13 04:34:21', '1716828031827.jpg');

-- --------------------------------------------------------

--
-- Table structure for table `classify_webcam`
--

CREATE TABLE `classify_webcam` (
  `id` int(11) NOT NULL,
  `webcam_token` varchar(10) NOT NULL,
  `mens_detected` int(11) NOT NULL,
  `womens_detected` int(11) NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `classify_webcam`
--

INSERT INTO `classify_webcam` (`id`, `webcam_token`, `mens_detected`, `womens_detected`, `timestamp`) VALUES
(1, '63c3fN9Y9W', 0, 1, '2024-06-11 03:45:25'),
(2, '63c3fN9Y9W', 0, 1, '2024-06-11 03:45:30'),
(3, '63c3fN9Y9W', 0, 1, '2024-06-11 03:45:35'),
(4, '63c3fN9Y9W', 0, 1, '2024-06-11 03:45:40'),
(5, '63c3fN9Y9W', 0, 1, '2024-06-11 03:45:45'),
(6, '63c3fN9Y9W', 0, 1, '2024-06-11 03:45:50'),
(7, '63c3fN9Y9W', 1, 0, '2024-06-11 03:45:55'),
(8, '63c3fN9Y9W', 0, 1, '2024-06-11 03:46:00'),
(9, '63c3fN9Y9W', 1, 0, '2024-06-11 03:46:05'),
(10, '63c3fN9Y9W', 1, 0, '2024-06-11 03:46:10'),
(11, '63c3fN9Y9W', 1, 0, '2024-06-11 03:46:15'),
(12, '63c3fN9Y9W', 1, 0, '2024-06-11 03:46:20'),
(13, '63c3fN9Y9W', 0, 1, '2024-06-11 03:46:25');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `classify_esp32`
--
ALTER TABLE `classify_esp32`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `classify_media`
--
ALTER TABLE `classify_media`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `classify_webcam`
--
ALTER TABLE `classify_webcam`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `classify_esp32`
--
ALTER TABLE `classify_esp32`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `classify_media`
--
ALTER TABLE `classify_media`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `classify_webcam`
--
ALTER TABLE `classify_webcam`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
