import {
  sqliteTable,
  text,
  integer,
  index,
  uniqueIndex,
} from 'drizzle-orm/sqlite-core';
export const visitors = sqliteTable(
  'visitors',
  {
    id: text().primaryKey(),
    tokenHash: text('token_hash').notNull(),
    ipHash: text('ip_hash').notNull(),
    createdAt: integer('created_at').notNull(),
  },
  (t) => [
    uniqueIndex('visitor_token').on(t.tokenHash),
    index('visitor_ip_date').on(t.ipHash, t.createdAt),
  ],
);
export const notes = sqliteTable(
  'notes',
  {
    id: text().primaryKey(),
    ownerId: text('owner_id').notNull(),
    world: text().notNull(),
    nickname: text().notNull(),
    body: text().notNull(),
    createdAt: integer('created_at').notNull(),
  },
  (t) => [
    index('notes_world_date').on(t.world, t.createdAt),
    index('notes_owner_date').on(t.ownerId, t.createdAt),
  ],
);
// Kept separate from every public note projection.
export const contacts = sqliteTable('contacts', {
  noteId: text('note_id').primaryKey(),
  email: text().notNull(),
  consentAt: integer('consent_at').notNull(),
});
export const mainHeads = sqliteTable('main_heads', {
  world: text().primaryKey(),
  revision: text().notNull(),
  data: text().notNull(),
  updatedAt: integer('updated_at').notNull(),
});
export const revisions = sqliteTable(
  'revisions',
  {
    id: text().primaryKey(),
    world: text().notNull(),
    parentId: text('parent_id'),
    proposalId: text('proposal_id'),
    data: text().notNull(),
    createdAt: integer('created_at').notNull(),
  },
  (t) => [index('revisions_world_date').on(t.world, t.createdAt)],
);
export const branches = sqliteTable(
  'branches',
  {
    id: text().primaryKey(),
    ownerId: text('owner_id').notNull(),
    world: text().notNull(),
    title: text().notNull(),
    sourceId: text('source_id'),
    baseRevision: text('base_revision').notNull(),
    baseData: text('base_data').notNull(),
    revision: integer().notNull(),
    data: text().notNull(),
    publishedRevision: integer('published_revision'),
    publishedData: text('published_data'),
    publishedBaseData: text('published_base_data'),
    publishedBaseRevision: text('published_base_revision'),
    publishedTitle: text('published_title'),
    createdAt: integer('created_at').notNull(),
    updatedAt: integer('updated_at').notNull(),
  },
  (t) => [
    index('branches_world_updated').on(t.world, t.updatedAt),
    index('branches_owner').on(t.ownerId),
  ],
);
export const branchVersions = sqliteTable(
  'branch_versions',
  {
    id: text().primaryKey(),
    branchId: text('branch_id').notNull(),
    revision: integer().notNull(),
    data: text().notNull(),
    createdAt: integer('created_at').notNull(),
  },
  (t) => [uniqueIndex('branch_version_unique').on(t.branchId, t.revision)],
);
export const proposals = sqliteTable(
  'proposals',
  {
    id: text().primaryKey(),
    title: text(),
    branchId: text('branch_id').notNull(),
    ownerId: text('owner_id').notNull(),
    world: text().notNull(),
    branchRevision: integer('branch_revision').notNull(),
    baseRevision: text('base_revision').notNull(),
    baseData: text('base_data').notNull(),
    data: text().notNull(),
    status: text().notNull(),
    mergedRevision: text('merged_revision'),
    createdAt: integer('created_at').notNull(),
  },
  (t) => [
    index('proposals_world_status').on(t.world, t.status),
    uniqueIndex('proposal_branch_revision').on(t.branchId, t.branchRevision),
  ],
);
export const credits = sqliteTable('credits', {
  ownerId: text('owner_id').primaryKey(),
  balanceMicros: integer('balance_micros').notNull().default(0),
});
export const ledger = sqliteTable(
  'ledger',
  {
    id: text().primaryKey(),
    ownerId: text('owner_id').notNull(),
    amountMicros: integer('amount_micros').notNull(),
    kind: text().notNull(),
    createdAt: integer('created_at').notNull(),
  },
  (t) => [index('ledger_owner_date').on(t.ownerId, t.createdAt)],
);

export const agentJobs = sqliteTable(
  'agent_jobs',
  {
    id: text().primaryKey(),
    ownerId: text('owner_id').notNull(),
    requestHash: text('request_hash').notNull(),
    status: text().notNull(),
    reservedMicros: integer('reserved_micros').notNull(),
    costMicros: integer('cost_micros'),
    result: text(),
    createdAt: integer('created_at').notNull(),
  },
  (t) => [index('agent_owner_date').on(t.ownerId, t.createdAt)],
);
