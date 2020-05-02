export const createVoteTable = `
DROP TABLE IF EXISTS votes;
CREATE TABLE IF NOT EXISTS votes (
  id SERIAL PRIMARY KEY,
  name VARCHAR DEFAULT '',
  vote VARCHAR NOT NULL
  )
  `;

export const insertVotes = `
INSERT INTO votes(name, vote)
VALUES ('chidimo', 'first vote'),
      ('orji', 'second vote')
`;

export const dropVotesTable = 'DROP TABLE votes';
