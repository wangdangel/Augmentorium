// UserService.scala
package com.example.service

import java.time.LocalDateTime
import scala.concurrent.{Future, ExecutionContext}
import scala.util.{Success, Failure}

import akka.actor.ActorSystem
import play.api.libs.json._
import play.api.libs.ws.WSClient
import cats.data.EitherT

import com.example.model.User
import com.example.repository.UserRepository

class UserService(
  userRepository: UserRepository,
  wsClient: WSClient
)(implicit ec: ExecutionContext, system: ActorSystem) {

  private val baseUrl = "https://api.example.com"
  
  def getUsers(): Future[Seq[User]] = {
    val url = s"$baseUrl/users"
    
    wsClient.url(url).get().flatMap { response =>
      if (response.status == 200) {
        val users = Json.parse(response.body).as[Seq[User]]
        // Cache users in repository
        userRepository.saveAll(users)
        Future.successful(users)
      } else {
        // Fallback to repository
        userRepository.findAll()
      }
    }.recoverWith {
      case _ => userRepository.findAll()
    }
  }
}