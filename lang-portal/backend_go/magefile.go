//go:build mage
// +build mage

package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"

	"lang-portal/internal/models"

	"github.com/magefile/mage/mg"
	"github.com/magefile/mage/sh"
	_ "github.com/mattn/go-sqlite3"
)

// Default target to run when none is specified
var Default = Run

// Install installs project dependencies
func Install() error {
	fmt.Println("Installing dependencies...")
	if err := sh.Run("go", "mod", "tidy"); err != nil {
		return err
	}
	return nil
}

// Run starts the development server
func Run() error {
	mg.Deps(Install)
	fmt.Println("Starting server...")
	log.Println("Starting database migration...")
	log.Println("Initializing services...")
	log.Println("Registering routes...")
	log.Println("Starting server on http://localhost:8081")
	cmd := exec.Command("go", "run", "cmd/server/main.go")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// Build builds the application
func Build() error {
	mg.Deps(Install)
	fmt.Println("Building...")
	return sh.Run("go", "build", "-o", "bin/server", "./cmd/server")
}

// InitDB initializes the database and runs migrations
func InitDB() error {
	fmt.Println("Initializing database...")

	// Initialize database
	db, err := models.NewDB("words.db")
	if err != nil {
		return fmt.Errorf("failed to open database: %v", err)
	}
	defer db.Close()

	migrationManager := db.NewMigrationManager(db.DB)
	if err := migrationManager.Initialize(); err != nil {
		log.Fatal("Failed to initialize migrations table:", err)
	}

	migrations, err := migrationManager.LoadMigrations("./migrations")
	if err != nil {
		log.Fatal("Failed to load migrations:", err)
	}

	if err := migrationManager.ApplyMigrations(migrations); err != nil {
		log.Fatal("Failed to apply migrations:", err)
	}

	fmt.Println("Database initialization completed successfully")
	return nil
}

// Seed seeds the database with initial data from JSON files
func Seed() error {
	fmt.Println("Seeding database...")

	// Initialize database
	db, err := models.NewDB("words.db")
	if err != nil {
		return fmt.Errorf("failed to open database: %v", err)
	}
	defer db.Close()

	// Insert seed data
	if _, err := db.Exec(`
		INSERT INTO words (japanese, romaji, french)
		VALUES 
		('こんにちは', 'konnichiwa', 'Bonjour),
		('さようなら', 'sayounara', 'Au revoir'),
		('ありがとう', 'arigatou', 'Merci')
	`); err != nil {
		return fmt.Errorf("failed to seed database: %v", err)
	}

	fmt.Println("Database seeding completed successfully")
	return nil
}

// Reset resets the database by removing the database file
func Reset() error {
	fmt.Println("Resetting database...")
	if err := os.Remove("words.db"); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("failed to remove database: %v", err)
	}
	fmt.Println("Database reset completed successfully")
	return nil
}

// ResetAndSeed resets the database and seeds it with initial data
func ResetAndSeed() error {
	mg.SerialDeps(Reset, InitDB, Seed)
	return nil
}

// TestDB initializes the test database with test data
func TestDB() error {
	fmt.Println("Initializing test database...")

	// Remove existing test database
	os.Remove("words.test.db")

	// Initialize database
	db, err := models.NewDB("words.test.db")
	if err != nil {
		return fmt.Errorf("failed to open test database: %v", err)
	}
	defer db.Close()

	// Apply schema
	schema, err := os.ReadFile("db/migrations/001_initial_schema.sql")
	if err != nil {
		return fmt.Errorf("failed to read schema: %v", err)
	}

	if _, err := db.Exec(string(schema)); err != nil {
		return fmt.Errorf("failed to apply schema: %v", err)
	}

	// Apply test data
	testData, err := os.ReadFile("db/test_data.sql")
	if err != nil {
		return fmt.Errorf("failed to read test data: %v", err)
	}

	if _, err := db.Exec(string(testData)); err != nil {
		return fmt.Errorf("failed to apply test data: %v", err)
	}

	fmt.Println("Test database initialized successfully")
	return nil
}
