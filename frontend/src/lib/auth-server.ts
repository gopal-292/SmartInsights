import { betterAuth } from "better-auth";
import { Pool } from "pg";

/**
 * Better Auth (PPT authentication stack) backed by PostgreSQL / Supabase.
 * Tables are created automatically on first use / migrate.
 */
export const auth = betterAuth({
  database: new Pool({
    connectionString:
      process.env.DATABASE_URL ||
      "postgresql://smartinsights:smartinsights@localhost:5433/smartinsights",
    connectionTimeoutMillis: 3000,
  }),
  emailAndPassword: {
    enabled: true,
  },
  user: {
    additionalFields: {},
  },
});

export type Session = typeof auth.$Infer.Session;
