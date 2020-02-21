#!/usr/bin/groovy

@Library(['github.com/indigo-dc/jenkins-pipeline-library@1.2.3']) _

pipeline {
    agent {
        label 'python'
    }

    environment {
        dockerhub_repo = "deephdc/deep-oc-mods"
        tf_ver = "1.14.0"
        dockerhub_repo = "ferag/xdc_lfw_frontend"
        py_ver = "py3"
    }
    
    stages {
        
         stage('Code fetching') {
            steps {
                checkout scm
            }
        }

        stage('Style analysis: PEP8') {
            steps {
                ToxEnvRun('pep8')
            }
            post {
                always {
                    warnings canComputeNew: false,
                             canResolveRelativePaths: false,
                             defaultEncoding: '',
                             excludePattern: '',
                             healthy: '',
                             includePattern: '',
                             messagesPattern: '',
                             parserConfigurations: [[parserName: 'PYLint', pattern: '**/flake8.log']],
                             unHealthy: ''
                    //WarningsReport('PYLint') // 'Flake8' fails..., consoleParsers does not produce any report...
                }
            }
        }

        stage('Docker image building') {
            agent {
                label 'docker-build'
            }
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
            agent {
                label 'docker-build'
            }
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
