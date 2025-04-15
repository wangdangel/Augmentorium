// NetworkManager.swift
import Foundation
import UIKit
import Combine

import Alamofire
import SwiftyJSON
import SDWebImage

class NetworkManager {
    private let baseURL = "https://api.example.com"
    private var cancellables = Set<AnyCancellable>()
    
    func fetchUsers() -> AnyPublisher<[User], Error> {
        let url = URL(string: "\(baseURL)/users")!
        
        return URLSession.shared.dataTaskPublisher(for: url)
            .map { $0.data }
            .decode(type: [User].self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }
    
    func downloadImage(from urlString: String, completion: @escaping (UIImage?) -> Void) {
        guard let url = URL(string: urlString) else {
            completion(nil)
            return
        }
        
        SDWebImageManager.shared.loadImage(with: url, options: [], progress: nil) { (image, _, _, _, _, _) in
            completion(image)
        }
    }
}