// UserService.m
#import "UserService.h"
#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>

#import <AFNetworking/AFNetworking.h>
#import "SDWebImage/SDWebImage.h"
#import <CocoaLumberjack/CocoaLumberjack.h>

@interface UserService ()
@property (nonatomic, strong) AFHTTPSessionManager *sessionManager;
@property (nonatomic, strong) NSString *baseURL;
@end

@implementation UserService

- (instancetype)init {
    self = [super init];
    if (self) {
        _baseURL = @"https://api.example.com";
        _sessionManager = [[AFHTTPSessionManager alloc] initWithBaseURL:[NSURL URLWithString:_baseURL]];
        _sessionManager.requestSerializer = [AFJSONRequestSerializer serializer];
        _sessionManager.responseSerializer = [AFJSONResponseSerializer serializer];
    }
    return self;
}

- (void)getUsersWithCompletion:(void (^)(NSArray *users, NSError *error))completion {
    [_sessionManager GET:@"/users" parameters:nil headers:nil progress:nil success:^(NSURLSessionDataTask * _Nonnull task, id  _Nullable responseObject) {
        if ([responseObject isKindOfClass:[NSArray class]]) {
            completion(responseObject, nil);
        } else {
            completion(nil, [NSError errorWithDomain:@"UserServiceError" code:1001 userInfo:@{NSLocalizedDescriptionKey: @"Invalid response format"}]);
        }
    } failure:^(NSURLSessionDataTask * _Nullable task, NSError * _Nonnull error) {
        completion(nil, error);
    }];
}

@end