import Model from '../models/model';

const votesModel = new Model('votes');
export const votesPage = async (req, res) => {
  try {
    const data = await votesModel.select('name, vote');
    res.status(200).json({ votes: data.rows });
  } catch (err) {
    res.status(200).json({ votes: err.stack });
  }
};
export const addVote = async (req, res) => {
  const { name, vote } = req.body;
  const columns = 'name, vote';
  const values = `'${name}', '${vote}'`;
  try {
    const data = await votesModel.insertWithReturn(columns, values);
    res.status(200).json({ votes: data.rows });
  } catch (err) {
    res.status(200).json({ votes: err.stack });
  }
};
