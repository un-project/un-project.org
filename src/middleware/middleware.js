export const modifyVote = (req, res, next) => {
  req.body.vote = `BLA: ${req.body.vote}`;
  next();
};
