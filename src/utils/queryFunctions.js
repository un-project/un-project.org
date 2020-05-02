import { pool } from '../models/pool';
import {
  insertVotes,
  dropVotesTable,
  createVoteTable,
} from './queries';

export const executeQueryArray = async arr => new Promise(resolve => {
  const stop = arr.length;
  arr.forEach(async (q, index) => {
    await pool.query(q);
    if (index + 1 === stop) resolve();
  });
});

export const dropTables = () => executeQueryArray([ dropVotesTable ]);
export const createTables = () => executeQueryArray([ createVoteTable ]);
export const insertIntoTables = () => executeQueryArray([ insertVotes ]);
