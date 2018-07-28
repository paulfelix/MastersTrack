CREATE TABLE IF NOT EXISTS `Athletes` (
  `athleteID` VARCHAR(64) NOT NULL,
  `firstName` VARCHAR(32) NOT NULL,
  `lastName` VARCHAR(32) NOT NULL,
  `gender` ENUM('M', 'W') NOT NULL,
  `birthYear` SMALLINT,
  PRIMARY KEY (`athleteID`),
  INDEX (`gender`)
);

CREATE TABLE IF NOT EXISTS `Meets` (
  `meetID` VARCHAR(32) NOT NULL,
  `season` ENUM('Indoor', 'Outdoor') NOT NULL,
  `year` SMALLINT NOT NULL,
  `startDate` DATE,
  `endDate` DATE,
  `city` VARCHAR(32),
  `state` VARCHAR(32),
  `country` VARCHAR(32),
  PRIMARY KEY (`meetID`),
  INDEX (`season`, `year`, `country`)
);

CREATE TABLE IF NOT EXISTS `Performances` (
  `meetID` VARCHAR(32) NOT NULL,
  `athleteID` VARCHAR(64) NOT NULL,
  `ageGroup` VARCHAR(4) NOT NULL,
  `event` VARCHAR(32) NOT NULL,
  `performance` FLOAT NOT NULL,
  `wind` VARCHAR(16),
  PRIMARY KEY (`meetID`, `athleteID`, `event`, `performance`),
  INDEX (`event`, `ageGroup`)
);
