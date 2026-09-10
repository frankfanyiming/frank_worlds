CREATE TABLE `branch_versions` (
	`id` text PRIMARY KEY NOT NULL,
	`branch_id` text NOT NULL,
	`revision` integer NOT NULL,
	`data` text NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `branch_version_unique` ON `branch_versions` (`branch_id`,`revision`);--> statement-breakpoint
CREATE TABLE `branches` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_id` text NOT NULL,
	`world` text NOT NULL,
	`title` text NOT NULL,
	`source_id` text,
	`base_revision` text NOT NULL,
	`base_data` text NOT NULL,
	`revision` integer NOT NULL,
	`data` text NOT NULL,
	`published_revision` integer,
	`published_data` text,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `branches_world_updated` ON `branches` (`world`,`updated_at`);--> statement-breakpoint
CREATE INDEX `branches_owner` ON `branches` (`owner_id`);--> statement-breakpoint
CREATE TABLE `contacts` (
	`note_id` text PRIMARY KEY NOT NULL,
	`email` text NOT NULL,
	`consent_at` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `credits` (
	`owner_id` text PRIMARY KEY NOT NULL,
	`balance_micros` integer DEFAULT 0 NOT NULL
);
--> statement-breakpoint
CREATE TABLE `ledger` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_id` text NOT NULL,
	`amount_micros` integer NOT NULL,
	`kind` text NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `ledger_owner_date` ON `ledger` (`owner_id`,`created_at`);--> statement-breakpoint
CREATE TABLE `main_heads` (
	`world` text PRIMARY KEY NOT NULL,
	`revision` text NOT NULL,
	`data` text NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `notes` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_id` text NOT NULL,
	`world` text NOT NULL,
	`nickname` text NOT NULL,
	`body` text NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `notes_world_date` ON `notes` (`world`,`created_at`);--> statement-breakpoint
CREATE INDEX `notes_owner_date` ON `notes` (`owner_id`,`created_at`);--> statement-breakpoint
CREATE TABLE `proposals` (
	`id` text PRIMARY KEY NOT NULL,
	`branch_id` text NOT NULL,
	`owner_id` text NOT NULL,
	`world` text NOT NULL,
	`branch_revision` integer NOT NULL,
	`base_revision` text NOT NULL,
	`base_data` text NOT NULL,
	`data` text NOT NULL,
	`status` text NOT NULL,
	`merged_revision` text,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `proposals_world_status` ON `proposals` (`world`,`status`);--> statement-breakpoint
CREATE UNIQUE INDEX `proposal_branch_revision` ON `proposals` (`branch_id`,`branch_revision`);--> statement-breakpoint
CREATE TABLE `revisions` (
	`id` text PRIMARY KEY NOT NULL,
	`world` text NOT NULL,
	`parent_id` text,
	`proposal_id` text,
	`data` text NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `revisions_world_date` ON `revisions` (`world`,`created_at`);--> statement-breakpoint
CREATE TABLE `visitors` (
	`id` text PRIMARY KEY NOT NULL,
	`token_hash` text NOT NULL,
	`ip_hash` text NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `visitor_token` ON `visitors` (`token_hash`);--> statement-breakpoint
CREATE INDEX `visitor_ip_date` ON `visitors` (`ip_hash`,`created_at`);