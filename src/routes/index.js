import express from 'express';
import { indexPage, votesPage, addVote } from '../controllers';
import { modifyVote } from '../middleware';
const indexRouter = express.Router();

indexRouter.get('/', indexPage);
indexRouter.get('/votes', votesPage)
indexRouter.post('/votes', modifyVote, addVote);

export default indexRouter;
