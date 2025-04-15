// app.js
import fs from 'fs';
import path from 'path';
import { promisify } from 'util';

import express from 'express';
import axios from 'axios';
import _ from 'lodash';

const readFile = promisify(fs.readFile);
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/api/users', async (req, res) => {
  try {
    const response = await axios.get('https://jsonplaceholder.typicode.com/users');
    const users = _.map(response.data, user => ({
      id: user.id,
      name: user.name,
      email: user.email
    }));
    
    res.json(users);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));