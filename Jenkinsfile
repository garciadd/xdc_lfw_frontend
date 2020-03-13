#!/usr/bin/groovy

@Library(['github.com/indigo-dc/jenkins-pipeline-library@1.2.3']) _

def job_result_url = ''

pipeline {
    agent {
        label 'python3.6'
    }

    environment {
        author_name = "Fernando Aguilar (CSIC)"
        author_email = "aguilarf@ifca.unican.es"
        app_name = "xdc_lfw_frontend"
        job_location = "Pipeline-as-code/XDC-wp2/xdc_lfw_integration_tests/${env.BRANCH_NAME}"
        dockerhub_repo = "extremedatacloud/xdc_lfw_frontend"
        py_ver = "py3"
    }
    
    stages {
        
         stage('Code fetching') {
            steps {
                checkout scm
            }
        }
        stage('Testing') {
            steps {
                ToxEnvRun('py36')
            }
        }
        stage('Style Analysis: PEP8') {
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
                script {
                    def job_result = JenkinsBuildJob("${env.job_location}")
                    job_result_url = job_result.absoluteUrl
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
                    script { //stage("Email notification")
                def build_status =  currentBuild.result
                build_status =  build_status ?: 'SUCCESS'
                def subject = """
New ${app_name} build in Jenkins@XDC:\
${build_status}: Job '${env.JOB_NAME}\
[${env.BUILD_NUMBER}]'"""

                def body = """
Dear ${author_name},\n\n
A new build of '${app_name} (${env.BRANCH_NAME})' XDC application is available in Jenkins at:\n\n
*  ${env.BUILD_URL}\n\n
terminated with '${build_status}' status.\n\n
Check console output at:\n\n
*  ${env.BUILD_URL}/console\n\n
and resultant Docker image rebuilding job at (may be empty in case of FAILURE):\n\n
*  ${job_result_url}\n\n
XDC Jenkins CI service"""

                EmailSend(subject, body, "${author_email}")
            }
                }
            }
        }
    }
}
