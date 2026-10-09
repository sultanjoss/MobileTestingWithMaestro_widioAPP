pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Check Workspace') {
            steps {
                bat 'dir'
            }
        }
    }
}