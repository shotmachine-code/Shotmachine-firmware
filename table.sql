-- MySQL dump 10.15  Distrib 10.0.28-MariaDB, for debian-linux-gnueabihf (armv7l)
--
-- Host: shotmachine    Database: shotmachine
-- ------------------------------------------------------
-- Server version	5.7.22

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `error_logs`
--

DROP TABLE IF EXISTS `error_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `error_logs` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `machine_id` bigint(20) unsigned NOT NULL,
  `error_id` int(10) unsigned NOT NULL,
  `description` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `error_logs_machine_id_foreign` (`machine_id`),
  KEY `error_logs_error_id_foreign` (`error_id`),
  CONSTRAINT `error_logs_error_id_foreign` FOREIGN KEY (`error_id`) REFERENCES `error_types` (`id`),
  CONSTRAINT `error_logs_machine_id_foreign` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `error_logs`
--

LOCK TABLES `error_logs` WRITE;
/*!40000 ALTER TABLE `error_logs` DISABLE KEYS */;
INSERT INTO `error_logs` VALUES (1,1,1,'Connection to database took longer than 5000 ms','2019-05-04 22:13:27','2019-05-04 22:13:27'),(2,1,1,'Connection to database took longer than 5000 ms','2019-05-04 22:14:27','2019-05-04 22:14:27'),(3,1,1,'Connection to database took longer than 5000 ms','2019-05-04 22:15:27','2019-05-04 22:15:27'),(4,1,1,'Connection to database took longer than 5000 ms','2019-05-04 22:16:27','2019-05-04 22:16:27'),(5,1,1,'Connection to database took longer than 5000 ms','2019-05-04 22:17:27','2019-05-04 22:17:27'),(6,1,1,'Connection to database took longer than 5000 ms','2019-05-04 22:18:27','2019-05-04 22:18:27'),(7,1,1,'Connection to database took longer than 5000 ms','2019-05-04 22:19:27','2019-05-04 22:19:27'),(8,1,1,'Connection to database took longer than 5000 ms','2019-05-04 22:20:27','2019-05-04 22:20:27'),(9,1,1,'Connection to database took longer than 5000 ms','2019-05-04 22:21:27','2019-05-04 22:21:27'),(10,1,2,'Connection to database failed','2019-05-04 22:20:27','2019-05-04 22:20:27'),(11,1,2,'Unknown column `id` in table `users` ','2019-05-04 22:22:27','2019-05-04 22:22:27');
/*!40000 ALTER TABLE `error_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `error_types`
--

DROP TABLE IF EXISTS `error_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `error_types` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `error_types`
--

LOCK TABLES `error_types` WRITE;
/*!40000 ALTER TABLE `error_types` DISABLE KEYS */;
INSERT INTO `error_types` VALUES (1,'warning','2019-06-07 18:42:51','2019-06-07 18:42:51'),(2,'critical','2019-06-07 18:42:51','2019-06-07 18:42:51');
/*!40000 ALTER TABLE `error_types` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-11-20 21:23:48
