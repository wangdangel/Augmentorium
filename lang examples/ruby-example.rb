# user_service.rb
require 'net/http'
require 'json'
require 'date'

require 'sinatra'
require 'httparty'
require 'dotenv/load'

class UserService
  API_URL = ENV['API_URL'] || 'https://api.example.com'
  
  def initialize
    @logger = Logger.new(STDOUT)
    @logger.level = Logger::INFO
  end
  
  def find_all
    @logger.info("Fetching all users at #{Time.now}")
    response = HTTParty.get("#{API_URL}/users", 
      headers: { "Content-Type" => "application/json" }
    )
    
    if response.success?
      JSON.parse(response.body)
    else
      @logger.error("Failed to fetch users: #{response.code}")
      []
    end
  end
  
  def find_by_id(id)
    response = HTTParty.get("#{API_URL}/users/#{id}")
    JSON.parse(response.body) if response.success?
  end
end