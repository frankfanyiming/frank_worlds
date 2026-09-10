CREATE TABLE `agent_jobs` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_id` text NOT NULL,
	`request_hash` text NOT NULL,
	`status` text NOT NULL,
	`reserved_micros` integer NOT NULL,
	`cost_micros` integer,
	`result` text,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `agent_owner_date` ON `agent_jobs` (`owner_id`,`created_at`);