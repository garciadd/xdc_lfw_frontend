#!/usr/bin/groovy

@Library(['github.com/indigo-dc/jenkins-pipeline-library@1.2.3']) _

pipeline {
    agent {
        label 'docker-build'
    }

    environment {
        dockerhub_repo = "extremedatacloud/xdc_lfw_frontend"
        py_ver = "py3"
    }

    stages {
        stage('Docker image building') {
            when {
                anyOf {
                    branch 'master'
                    branch 'test'
                    buildingTag()
                }
            }
            steps{
                script {
                    id = "${env.dockerhub_repo}"
                    
                    if (env.BRANCH_NAME == 'master') {
                        // CPU
                        id_cpu = DockerBuild(
                            id,
                            tag: ['latest'],
                            build_args: [
                                "py_ver=${env.py_ver}",
                                "branch=master"
                            ]
                        )
                    }
                    if (env.BRANCH_NAME == 'test') {
                        // CPU
                        id_cpu = DockerBuild(
                            id,
                            tag: ['test'],
                            build_args: [
                                "py_ver=${env.py_ver}",
                                "branch=test"
                            ]
                        )
                    }
                }
            }
        }
        
        stage('Docker Hub delivery') {
            when {
                anyOf {
                    branch 'master'
                    branch 'test'
                    buildingTag()
                }
            }
            steps {
                script {
                    DockerPush(id_cpu)
                }
            }
            post {
                failure {
                    DockerClean()
                }
                always {
                    cleanWs()
                }
            }
        }
    }
}
