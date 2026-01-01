// MongoDB initialization script
// This script runs when MongoDB container is first started
// It creates the initial database, collections, and indexes

// Switch to the app database
db = db.getSiblingDB('appdb');

// Create collections with validation schemas
print("Initializing MongoDB database...");

// Users collection
db.createCollection("users", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["email", "username", "createdAt"],
            properties: {
                email: {
                    bsonType: "string",
                    pattern: "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$",
                    description: "Must be a valid email address"
                },
                username: {
                    bsonType: "string",
                    minLength: 3,
                    maxLength: 50,
                    description: "Username must be between 3 and 50 characters"
                },
                passwordHash: {
                    bsonType: "string",
                    description: "Hashed password"
                },
                isActive: {
                    bsonType: "bool",
                    description: "Whether user account is active"
                },
                role: {
                    bsonType: "string",
                    enum: ["user", "admin", "moderator"],
                    description: "User role"
                },
                createdAt: {
                    bsonType: "date",
                    description: "Creation timestamp"
                },
                updatedAt: {
                    bsonType: "date",
                    description: "Last update timestamp"
                }
            }
        }
    }
});

// Sessions collection for authentication
db.createCollection("sessions", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["userId", "token", "expiresAt", "createdAt"],
            properties: {
                userId: {
                    bsonType: "objectId",
                    description: "Reference to user"
                },
                token: {
                    bsonType: "string",
                    description: "Session token"
                },
                ipAddress: {
                    bsonType: "string",
                    description: "Client IP address"
                },
                userAgent: {
                    bsonType: "string",
                    description: "Client user agent"
                },
                expiresAt: {
                    bsonType: "date",
                    description: "Session expiration time"
                },
                createdAt: {
                    bsonType: "date",
                    description: "Creation timestamp"
                }
            }
        }
    }
});

// Refresh tokens collection
db.createCollection("refreshTokens", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["userId", "token", "expiresAt", "createdAt"],
            properties: {
                userId: {
                    bsonType: "objectId",
                    description: "Reference to user"
                },
                token: {
                    bsonType: "string",
                    description: "Refresh token"
                },
                isRevoked: {
                    bsonType: "bool",
                    description: "Whether token has been revoked"
                },
                expiresAt: {
                    bsonType: "date",
                    description: "Token expiration time"
                },
                createdAt: {
                    bsonType: "date",
                    description: "Creation timestamp"
                }
            }
        }
    }
});

// OTP codes collection
db.createCollection("otpCodes", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["code", "purpose", "expiresAt", "createdAt"],
            properties: {
                code: {
                    bsonType: "string",
                    description: "OTP code"
                },
                purpose: {
                    bsonType: "string",
                    enum: ["email_verification", "password_reset", "login"],
                    description: "OTP purpose"
                },
                userId: {
                    bsonType: "objectId",
                    description: "Reference to user"
                },
                email: {
                    bsonType: "string",
                    description: "Email for sending OTP"
                },
                isUsed: {
                    bsonType: "bool",
                    description: "Whether code has been used"
                },
                expiresAt: {
                    bsonType: "date",
                    description: "Code expiration time"
                },
                createdAt: {
                    bsonType: "date",
                    description: "Creation timestamp"
                }
            }
        }
    }
});

// Create indexes
print("Creating indexes...");

// Users indexes
db.users.createIndex({ "email": 1 }, { unique: true, sparse: true });
db.users.createIndex({ "username": 1 }, { unique: true, sparse: true });
db.users.createIndex({ "createdAt": -1 });
db.users.createIndex({ "isActive": 1 });

// Sessions indexes
db.sessions.createIndex({ "userId": 1 });
db.sessions.createIndex({ "token": 1 }, { unique: true });
db.sessions.createIndex({ "expiresAt": 1 }, { expireAfterSeconds: 0 });
db.sessions.createIndex({ "createdAt": -1 });

// Refresh tokens indexes
db.refreshTokens.createIndex({ "userId": 1 });
db.refreshTokens.createIndex({ "token": 1 }, { unique: true });
db.refreshTokens.createIndex({ "expiresAt": 1 }, { expireAfterSeconds: 0 });
db.refreshTokens.createIndex({ "isRevoked": 1, "expiresAt": 1 });

// OTP codes indexes
db.otpCodes.createIndex({ "code": 1 });
db.otpCodes.createIndex({ "userId": 1 });
db.otpCodes.createIndex({ "email": 1 });
db.otpCodes.createIndex({ "expiresAt": 1 }, { expireAfterSeconds: 0 });
db.otpCodes.createIndex({ "isUsed": 1, "expiresAt": 1 });

// Create admin user (optional - remove or secure in production)
print("Creating admin user...");
db.users.insertOne({
    email: "admin@example.com",
    username: "admin",
    passwordHash: "$2b$12$placeholder_hash_replace_in_production",
    isActive: true,
    role: "admin",
    createdAt: new Date(),
    updatedAt: new Date()
});

print("MongoDB initialization complete!");
print("Database: appdb");
print("Collections created: users, sessions, refreshTokens, otpCodes");
