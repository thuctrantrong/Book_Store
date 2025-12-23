-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: bookstore
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
-- Temporary view structure for view `vw_book_main`
--

DROP TABLE IF EXISTS `vw_book_main`;
/*!50001 DROP VIEW IF EXISTS `vw_book_main`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_book_main` AS SELECT 
 1 AS `book_id`,
 1 AS `title`,
 1 AS `price`,
 1 AS `avg_rating`,
 1 AS `rating_count`,
 1 AS `status`,
 1 AS `publication_year`,
 1 AS `format`,
 1 AS `main_image`,
 1 AS `author_name`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_user_category_counts`
--

DROP TABLE IF EXISTS `vw_user_category_counts`;
/*!50001 DROP VIEW IF EXISTS `vw_user_category_counts`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_user_category_counts` AS SELECT 
 1 AS `user_id`,
 1 AS `category_id`,
 1 AS `cnt`*/;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `vw_book_main`
--

/*!50001 DROP VIEW IF EXISTS `vw_book_main`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_book_main` AS select `t`.`book_id` AS `book_id`,`t`.`title` AS `title`,`t`.`price` AS `price`,`t`.`avg_rating` AS `avg_rating`,`t`.`rating_count` AS `rating_count`,`t`.`status` AS `status`,`t`.`publication_year` AS `publication_year`,`t`.`format` AS `format`,`t`.`main_image` AS `main_image`,`t`.`author_name` AS `author_name` from (select `b`.`book_id` AS `book_id`,`b`.`title` AS `title`,`b`.`price` AS `price`,`b`.`avg_rating` AS `avg_rating`,`b`.`rating_count` AS `rating_count`,`b`.`status` AS `status`,`b`.`publication_year` AS `publication_year`,`b`.`format` AS `format`,`a`.`author_name` AS `author_name`,`bi`.`image_url` AS `main_image`,row_number() OVER (PARTITION BY `b`.`book_id` ORDER BY `bi`.`is_main` desc,`bi`.`image_id` )  AS `rn` from ((`books` `b` left join `authors` `a` on((`a`.`author_id` = `b`.`author_id`))) left join `book_images` `bi` on((`bi`.`book_id` = `b`.`book_id`))) where ((`b`.`status` = 'active') and (`b`.`stock_quantity` > 0))) `t` where (`t`.`rn` = 1) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_user_category_counts`
--

/*!50001 DROP VIEW IF EXISTS `vw_user_category_counts`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_user_category_counts` AS select `o`.`user_id` AS `user_id`,`bc`.`category_id` AS `category_id`,sum(`od`.`quantity`) AS `cnt` from ((`orders` `o` join `order_details` `od` on((`o`.`order_id` = `od`.`order_id`))) join `book_categories` `bc` on((`od`.`book_id` = `bc`.`book_id`))) where (`o`.`status` in ('processing','shipped','delivered')) group by `o`.`user_id`,`bc`.`category_id` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-23 14:01:10
