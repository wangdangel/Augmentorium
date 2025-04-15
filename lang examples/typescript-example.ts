// api-client.ts
import axios, { AxiosResponse, AxiosRequestConfig } from 'axios';
import { createLogger } from 'winston';
import * as dotenv from 'dotenv';

dotenv.config();

interface User {
  id: number;
  name: string;
  email: string;
}

interface ApiResponse<T> {
  data: T;
  status: number;
  message: string;
}

const logger = createLogger({
  level: 'info',
  transports: [/* transport configuration */]
});

export class ApiClient {
  private baseUrl: string = process.env.API_URL || 'https://api.example.com';
  
  async getUsers(): Promise<ApiResponse<User[]>> {
    try {
      const response: AxiosResponse = await axios.get(`${this.baseUrl}/users`);
      logger.info('Users fetched successfully');
      return { data: response.data, status: 200, message: 'Success' };
    } catch (error) {
      logger.error('Error fetching users', error);
      throw error;
    }
  }
}