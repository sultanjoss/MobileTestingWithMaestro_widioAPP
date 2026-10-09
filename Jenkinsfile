pipeline {
    agent any

    environment {
        JAVA_HOME = 'C:\\Program Files\\Java\\jdk-26.0.2.1'
        ANDROID_HOME = 'C:\\Users\\Surface\\AppData\\Local\\Android\\Sdk'

        PATH = "C:\\Users\\Surface\\scoop\\shims;" +
               "C:\\Program Files\\Java\\jdk-26.0.2.1\\bin;" +
               "C:\\Users\\Surface\\AppData\\Local\\Android\\Sdk\\platform-tools;" +
               "C:\\Users\\Surface\\AppData\\Local\\Android\\Sdk\\emulator;" +
               "C:\\maestro\\maestro\\bin;" +
               "${env.PATH}"
    }

    stages {

        stage('Check Tools') {
            steps {
                bat 'git --version'
                bat 'java -version'
                bat 'adb version'
                bat 'maestro --version'
            }
        }

        stage('Check Android Device') {
            steps {
                bat 'adb devices'
            }
        }

        stage('Run Maestro Positive Test') {
            steps {bat '''if not exist reports mkdir reports
            maestro test flowslogin ^
            --include-tags=positif ^
            --format junit ^
            --output reports\\maestro-positive-result.xml
            '''
            }
        }
        stage('Publish Test Result') {
            steps {junit 'reports/maestro-positive-result.xml'
            }
        }
    }
}