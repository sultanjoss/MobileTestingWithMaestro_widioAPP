pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Check Tools') {
            steps {
                bat 'git --version'
                bat 'java -version'
                bat 'maestro --version'
                bat 'adb devices'
            }
        }

        stage('Run Maestro Smoke Test') {
            steps {
                bat 'maestro test . --include-tags=smoke'
            }
        }

    }
}