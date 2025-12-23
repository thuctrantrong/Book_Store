-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: test
-- ------------------------------------------------------
-- Server version	9.4.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories` (
  `category_id` int NOT NULL AUTO_INCREMENT,
  `category_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` enum('active','inactive','deleted') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_by` int DEFAULT NULL,
  `deleted_by` int DEFAULT NULL,
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `category_name` (`category_name`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (1,'Công nghệ - Kỹ thuật','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(2,'Giáo dục - Giáo trình','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(3,'Hồi ký - Tự truyện','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(4,'Khoa học tự nhiên','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(5,'Khoa học xã hội','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(6,'Kinh doanh - Kinh tế','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(7,'Kinh dị - Thriller','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(8,'Kỹ năng sống - Phát triển bản thân','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(9,'Lịch sử','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(10,'Ngôn tình - Lãng mạn','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(11,'Pháp luật - Chính trị','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(12,'Thiếu nhi','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(13,'Tiên hiệp - Huyền huyễn','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(14,'Trinh thám - Pháp y','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(15,'Triết học','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(16,'Truyện tranh','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(17,'Tâm lý học','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(18,'Tôn giáo - Tâm linh','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(19,'Võng du','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(20,'Văn học - Thơ - Tản văn','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(21,'Văn học - Tiểu thuyết','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL),(22,'Xuyên không - Trọng sinh','active','2025-12-05 13:43:49','2025-12-05 13:43:49',NULL,NULL);
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-23 13:47:53
