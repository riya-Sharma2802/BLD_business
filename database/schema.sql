-- Business Listings Dashboard - schema
CREATE DATABASE IF NOT EXISTS listings_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE listings_db;

CREATE TABLE IF NOT EXISTS listing_master (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  business_name VARCHAR(255) NOT NULL,
  category      VARCHAR(120) NOT NULL,
  city          VARCHAR(100) NOT NULL,
  address       VARCHAR(500) NULL,
  phone         VARCHAR(30)  NULL,
  source        VARCHAR(80)  NOT NULL,
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  -- Prevents the same listing being inserted twice from the same source
  UNIQUE KEY uq_listing (business_name, address(255), source),
  -- Indexes speed up the GROUP BY aggregations used by the dashboard
  KEY idx_city (city),
  KEY idx_category (category),
  KEY idx_source (source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
