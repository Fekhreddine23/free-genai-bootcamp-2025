
// static functions for validating options for various classes
class OptsValidator {
    /**
     * Validates that an option exists and is not undefined
     * @param {Object} options - The options object
     * @param {string} key - The key to check
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the option doesn't exist
     */
    static required(options, key, errorMessage) {
        if (options[key] === undefined) {
            throw new Error(errorMessage || `${key} is required`);
        }
    }

    /**
     * Validates that an option is a string
     * @param {Object} options - The options object
     * @param {string} key - The key to check
     * @param {boolean} [required=false] - Whether the option is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the option is not a string
     */
    static string(options, key, required = false, errorMessage) {
        if (required) {
            this.required(options, key, `${key} is required and must be a string`);
        }
        
        if (options[key] !== undefined && typeof options[key] !== 'string') {
            throw new Error(errorMessage || `${key} must be a string`);
        }
    }

    /**
     * Validates that an option is a number
     * @param {Object} options - The options object
     * @param {string} key - The key to check
     * @param {boolean} [required=false] - Whether the option is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the option is not a number
     */
    static number(options, key, required = false, errorMessage) {
        if (required) {
            this.required(options, key, `${key} is required and must be a number`);
        }
        
        if (options[key] !== undefined && typeof options[key] !== 'number') {
            throw new Error(errorMessage || `${key} must be a number`);
        }
    }

    /**
     * Validates that an option is a boolean
     * @param {Object} options - The options object
     * @param {string} key - The key to check
     * @param {boolean} [required=false] - Whether the option is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the option is not a boolean
     */
    static boolean(options, key, required = false, errorMessage) {
        if (required) {
            this.required(options, key, `${key} is required and must be a boolean`);
        }
        
        if (options[key] !== undefined && typeof options[key] !== 'boolean') {
            throw new Error(errorMessage || `${key} must be a boolean`);
        }
    }

    /**
     * Validates that an option is a function
     * @param {Object} options - The options object
     * @param {string} key - The key to check
     * @param {boolean} [required=false] - Whether the option is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the option is not a function
     */
    static function(options, key, required = false, errorMessage) {
        if (required) {
            this.required(options, key, `${key} is required and must be a function`);
        }
        
        if (options[key] !== undefined && typeof options[key] !== 'function') {
            throw new Error(errorMessage || `${key} must be a function`);
        }
    }

    /**
     * Validates that an option is an object
     * @param {Object} options - The options object
     * @param {string} key - The key to check
     * @param {boolean} [required=false] - Whether the option is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the option is not an object
     */
    static object(options, key, required = false, errorMessage) {
        if (required) {
            this.required(options, key, `${key} is required and must be an object`);
        }
        
        if (options[key] !== undefined && (typeof options[key] !== 'object' || options[key] === null || Array.isArray(options[key]))) {
            throw new Error(errorMessage || `${key} must be an object`);
        }
    }

    /**
     * Validates that an option is an array
     * @param {Object} options - The options object
     * @param {string} key - The key to check
     * @param {boolean} [required=false] - Whether the option is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the option is not an array
     */
    static array(options, key, required = false, errorMessage) {
        if (required) {
            this.required(options, key, `${key} is required and must be an array`);
        }
        
        if (options[key] !== undefined && !Array.isArray(options[key])) {
            throw new Error(errorMessage || `${key} must be an array`);
        }
    }
    
    /**
     * Validates that an array has at least a minimum number of items
     * @param {Object} options - The options object
     * @param {string} key - The key to check
     * @param {number} minLength - The minimum length required
     * @param {boolean} [required=false] - Whether the option is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the array doesn't have the minimum length
     */
    static arrayMinLength(options, key, minLength, required = false, errorMessage) {
        this.array(options, key, required);
        
        if (options[key] !== undefined && options[key].length < minLength) {
            throw new Error(errorMessage || `${key} must be an array with at least ${minLength} items`);
        }
    }
    
    /**
     * Validates that an index is within the bounds of an array
     * @param {Object} options - The options object
     * @param {string} indexKey - The key for the index value
     * @param {string} arrayKey - The key for the array
     * @param {boolean} [required=false] - Whether the index is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the index is out of bounds
     */
    static indexInBounds(options, indexKey, arrayKey, required = false, errorMessage) {
        if (required) {
            this.required(options, indexKey, `${indexKey} is required`);
        }
        
        if (options[indexKey] !== undefined) {
            this.number(options, indexKey);
            this.array(options, arrayKey, true);
            
            if (options[indexKey] < 0 || options[indexKey] >= options[arrayKey].length) {
                throw new Error(errorMessage || `${indexKey} must be between 0 and ${options[arrayKey].length - 1}`);
            }
        }
    }
    
    /**
     * Validates that a numeric value is within a specified range
     * @param {Object} options - The options object
     * @param {string} valueKey - The key for the value to check
     * @param {string} minKey - The key for the minimum value
     * @param {string} maxKey - The key for the maximum value
     * @param {boolean} [required=false] - Whether the value is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the value is not within the range
     */
    static numberInRange(options, valueKey, minKey, maxKey, required = false, errorMessage) {
        if (required) {
            this.required(options, valueKey, `${valueKey} is required`);
        }
        
        if (options[valueKey] !== undefined) {
            this.number(options, valueKey);
            this.number(options, minKey, true);
            this.number(options, maxKey, true);
            
            if (options[valueKey] < options[minKey] || options[valueKey] > options[maxKey]) {
                throw new Error(errorMessage || `${valueKey} must be between ${options[minKey]} and ${options[maxKey]}`);
            }
        }
    }
    
    /**
     * Validates that a maximum value is greater than a minimum value
     * @param {Object} options - The options object
     * @param {string} maxKey - The key for the maximum value
     * @param {string} minKey - The key for the minimum value
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the maximum value is not greater than the minimum value
     */
    static maxGreaterThanMin(options, maxKey, minKey, errorMessage) {
        this.number(options, maxKey, true);
        this.number(options, minKey, true);
        
        if (options[maxKey] <= options[minKey]) {
            throw new Error(errorMessage || `${maxKey} must be greater than ${minKey}`);
        }
    }

    /**
     * Validates that an option is an array with a specific length
     * @param {Object} options - The options object
     * @param {string} key - The key to check
     * @param {number} length - The required length of the array
     * @param {boolean} [required=false] - Whether the option is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the option is not an array with the specified length
     */
    static arrayLength(options, key, length, required = false, errorMessage) {
        this.array(options, key, required);
        
        if (options[key] !== undefined && options[key].length !== length) {
            throw new Error(errorMessage || `${key} must be an array with ${length} elements`);
        }
    }

    /**
     * Validates that an option is an array of numbers
     * @param {Object} options - The options object
     * @param {string} key - The key to check
     * @param {boolean} [required=false] - Whether the option is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the option is not an array of numbers
     */
    static arrayOfNumbers(options, key, required = false, errorMessage) {
        this.array(options, key, required);
        
        if (options[key] !== undefined) {
            for (let i = 0; i < options[key].length; i++) {
                if (typeof options[key][i] !== 'number') {
                    throw new Error(errorMessage || `${key} must be an array of numbers`);
                }
            }
        }
    }

    /**
     * Validates that an option is an array of strings
     * @param {Object} options - The options object
     * @param {string} key - The key to check
     * @param {boolean} [required=false] - Whether the option is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the option is not an array of strings
     */
    static arrayOfStrings(options, key, required = false, errorMessage) {
        this.array(options, key, required);
        
        if (options[key] !== undefined) {
            for (let i = 0; i < options[key].length; i++) {
                if (typeof options[key][i] !== 'string') {
                    throw new Error(errorMessage || `${key} must be an array of strings`);
                }
            }
        }
    }

    /**
     * Validates that an option is one of a set of allowed values
     * @param {Object} options - The options object
     * @param {string} key - The key to check
     * @param {Array} allowedValues - The allowed values
     * @param {boolean} [required=false] - Whether the option is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the option is not one of the allowed values
     */
    static oneOf(options, key, allowedValues, required = false, errorMessage) {
        if (required) {
            this.required(options, key, `${key} is required and must be one of: ${allowedValues.join(', ')}`);
        }
        
        if (options[key] !== undefined && !allowedValues.includes(options[key])) {
            throw new Error(errorMessage || `${key}: (${options[key]}) must be one of: ${allowedValues.join(', ')}`);
        }
    }

    /**
     * Validates a position array [x, y]
     * @param {Object} options - The options object
     * @param {string} key - The key to check (typically 'position')
     * @param {boolean} [required=false] - Whether the option is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the position is not valid
     */
    static position(options, key = 'position', required = false, errorMessage) {
        this.array(options, key, required, `${key} must be an array with format [x, y]`);
        
        if (options[key] !== undefined) {
            this.arrayLength(options, key, 2, false, `${key} must be an array with format [x, y]`);
            this.arrayOfNumbers(options, key, false, `${key} must contain numeric values for x and y`);
        }
    }

    /**
     * Validates a size array [width, height]
     * @param {Object} options - The options object
     * @param {string} key - The key to check (typically 'size')
     * @param {boolean} [required=false] - Whether the option is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the size is not valid
     */
    static size(options, key = 'size', required = false, errorMessage) {
        this.array(options, key, required, `${key} must be an array with format [width, height]`);
        
        if (options[key] !== undefined) {
            this.arrayLength(options, key, 2, false, `${key} must be an array with format [width, height]`);
            this.arrayOfNumbers(options, key, false, `${key} must contain numeric values for width and height`);
        }
    }

    /**
     * Validates a color string (doesn't check format, just that it's a string)
     * @param {Object} options - The options object
     * @param {string} key - The key to check (typically 'color')
     * @param {boolean} [required=false] - Whether the option is required
     * @param {string} [errorMessage] - Optional custom error message
     * @throws {Error} If the color is not valid
     */
    static color(options, key = 'color', required = false, errorMessage) {
        this.string(options, key, required, errorMessage || `${key} must be a valid color string`);
    }

    /**
     * Validates multiple options at once
     * @param {Object} options - The options object
     * @param {Object} schema - The validation schema
     * @throws {Error} If any validation fails
     * 
     * Example schema:
     * {
     *   text: { type: 'string', required: true },
     *   position: { type: 'position', required: true },
     *   size: { type: 'size', required: true },
     *   color: { type: 'color' },
     *   onClick: { type: 'function' },
     *   values: { type: 'array', minLength: 2, required: true },
     *   initialIndex: { type: 'indexInBounds', arrayKey: 'values' }
     * }
     */
    static validate(options, schema) {
        for (const key in schema) {
            const validation = schema[key];
            const required = validation.required || false;
            const type = validation.type;
            const errorMessage = validation.message;
            
            switch (type) {
                case 'string':
                    this.string(options, key, required, errorMessage);
                    break;
                case 'number':
                    this.number(options, key, required, errorMessage);
                    break;
                case 'boolean':
                    this.boolean(options, key, required, errorMessage);
                    break;
                case 'function':
                    this.function(options, key, required, errorMessage);
                    break;
                case 'object':
                    this.object(options, key, required, errorMessage);
                    break;
                case 'array':
                    this.array(options, key, required, errorMessage);
                    // Check for minimum length if specified
                    if (validation.minLength !== undefined && options[key] !== undefined) {
                        this.arrayMinLength(options, key, validation.minLength, false, validation.minLengthMessage || errorMessage);
                    }
                    break;
                case 'position':
                    this.position(options, key, required, errorMessage);
                    break;
                case 'size':
                    this.size(options, key, required, errorMessage);
                    break;
                case 'color':
                    this.color(options, key, required, errorMessage);
                    break;
                case 'oneOf':
                    this.oneOf(options, key, validation.values, required, errorMessage);
                    break;
                case 'indexInBounds':
                    this.indexInBounds(options, key, validation.arrayKey, required, errorMessage);
                    break;
                case 'numberInRange':
                    this.numberInRange(options, key, validation.minKey, validation.maxKey, required, errorMessage);
                    break;
                case 'maxGreaterThanMin':
                    this.maxGreaterThanMin(options, key, validation.minKey, errorMessage);
                    break;

                default:
                    throw new Error(`Unknown validation type: ${type}`);
            }
        }
    }
}

if (typeof window !== 'undefined') {
    window.OptsValidator = OptsValidator;
}