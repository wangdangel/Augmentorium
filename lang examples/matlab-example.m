% image_processor.m
function processed_image = image_processor(input_image)
    % Import required packages
    import matlab.io.*
    import matlab.image.*
    addpath('./utils');
    
    % Check input validity
    if nargin < 1
        error('Input image required');
    end
    
    % Load image if filename is provided
    if ischar(input_image) || isstring(input_image)
        try
            input_image = imread(input_image);
        catch ME
            error('Failed to load image file: %s', ME.message);
        end
    end
    
    % Convert to grayscale if RGB
    if size(input_image, 3) == 3
        gray_image = rgb2gray(input_image);
    else
        gray_image = input_image;
    end
    
    % Apply Gaussian filter for noise reduction
    filtered_image = imgaussfilt(gray_image, 2);
    
    % Edge detection
    processed_image = edge(filtered_image, 'Canny');
end