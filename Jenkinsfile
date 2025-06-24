pipeline {
    agent any

    environment {
        FEATURE_BRANCH = "${env.BRANCH_NAME}"
        TARGET_BRANCH = "develop"
        ORCHESTRATION_DIR = "OrchestrationPipeline"
        DOCKER_CREDENTIALS_ID = 'dockerhub-creds'
        KUBECONFIG = '/var/lib/jenkins/.kube/config'
        GIT_REPO = 'ci-user@INTERNAL_HOST:/home/ci-user/git/Gruppo3.git'
        GIT_CREDENTIALS_ID = 'ci-user'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "**"]],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [],
                    userRemoteConfigs: [[
                        url: "${env.GIT_REPO}",
                        credentialsId: "${env.GIT_CREDENTIALS_ID}",
                        refspec: '+refs/heads/*:refs/remotes/origin/*'
                    ]]
                ])
            }
        }

        stage('Check [ci skip]') {
            steps {
                script {
                    def commitMsg = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
                    if (commitMsg.contains('[ci skip]')) {
                        echo "Commit contiene [ci skip]: la pipeline verrà saltata."
                        return
                    }
                }
            }
        }

        stage('Pulizia Workspace') {
            steps {
                deleteDir()
                echo "Pulizia workspace completata."
            }
        }

        stage('Orchestrator') {
            steps {
                script {
                    def stepsFeature = [
                        //CI-Feature 
                        "setupBot.jenkins", //setup bot per gestione git automatizzato con Jenkins
                        "changedService.jenkins", // rileva e marca i servizi con modifica
                        "validateStructure.jenkins", //validazione struttura cartelle e contenuti necessari servizio (k8s, dockerfile,tests)
                        "buildDocker.jenkins", //load e test docker image e push su registry, se gia presenta istanza elimina e riloada. 
                        "validateFeature.jenkins", //run e chiusura immagini pipeline di validazione feature branch (incluso Frontend seppure molto semplice)

                        //CI-PreDevelop
                        "mergeOnDevelop.jenkins", //merge feature branch da develop, in caso di conflitti blocca
                        "systemStaging.jenkins", //deploy del sistema su ambiente staging (sfrutta un file yaml k8s piu leggero e carica anche Frontend, ma con namespace diverso e con type:ClusterIp)
                        "integrationTests.jenkins", //test integrazione dopo merge
                        "securityTest.jenkins", //Lancia tool per analisi vulnerabilità e chiude il sistema su staging dopo test
                        "pushOnDevelop.jenkins" //push automatico su remote develop branch 
                    ]

                    def stepsDevelop = [
                        //CD-Develop
                        "preReleaseStaging.jenkins", //deploy del sistema su ambiente staging (sfrutta stesso file k8s di deploy e carica anche Frontend, ma con namespace diverso e con Ingress Nginx)
                        "approvalToMaster.jenkins", // approvazione con code review obbligatoria e testing e2e manuale e notificata ai membri del team per email, si mette in attesa di approvazione
                        "smokeTests.jenkins", //Esegue test di disponibilità dopo l'approvazione manuale e chiude il sistema su staging 
                        "performanceTest.jenkins", //Esegue benchmark o load test (Newman) dopo l'apporvazione manuale (test di scalabilità e performance)
                        "pushToMaster.jenkins"  //merge e push develop->main (master) , blocco pipeline in caso di errore
                    ]
                    
                    def stepsMaster = [
                        //CD-Master
                        "deployProduction.jenkins", //deploy produzione su main
                        "smokeTests.jenkins", //in caso di fallimento qui ripristina lo stato precedente del deploy (es. usando kubectl rollout undo)
                        "performanceTest.jenkins", //in caso di fallimento qui ripristina lo stato precedente del deploy (es. usando kubectl rollout undo)
                        "generatePackageDiagram.jenkins" //Genera il diagramma dei pacchetti del progetto (es. con PlantUML)
                    ]

                    if (!(env.BRANCH_NAME in ["develop", "origin/develop", "main", "origin/main", "master", "origin/master"])) {
                        stepsFeature.each { fileName ->
                            def filePath = "${ORCHESTRATION_DIR}/${fileName}"
                            echo "Caricando ed eseguendo SOLO SU FEATURE: ${filePath}"
                            load filePath
                        }
                    } else if (env.BRANCH_NAME in ["develop", "origin/develop"]) {
                        stepsDevelop.each { fileName ->
                            def filePath = "${ORCHESTRATION_DIR}/${fileName}"
                            echo "Caricando ed eseguendo SOLO SU develop: ${filePath}"
                            load filePath
                        }
                    } else if (env.BRANCH_NAME in ["main", "origin/main", "master", "origin/master"]) {
                        stepsMaster.each { fileName ->
                            def filePath = "${ORCHESTRATION_DIR}/${fileName}"
                            echo "Caricando ed eseguendo SOLO SU master: ${filePath}"
                            load filePath
                        }
                    }
                }
            }
        }
    }

    post {
        failure {
            script {
                echo "Pipeline fallita su ${env.BRANCH_NAME}"
                echo "Pulizia risorse..."
                sh "microk8s kubectl delete namespace staging --wait=true || true"
                sh "microk8s kubectl delete namespace pre-release --wait=true || true"
                load "${ORCHESTRATION_DIR}/notificationsFailure.jenkins" //modulo per notifiche email/slack ecc di failure al pusher
            }
        }
        success {
            script {
                echo "Pipeline completata con successo su ${env.BRANCH_NAME}"
                echo "Pulizia risorse in eccesso..." //ci si assicura che non ci siano risorse residue dopo il deploy o dopo aver compiuto le azioni desiderate che possano occupare spazio
                sh "microk8s kubectl delete namespace staging --wait=true || true"
                sh "microk8s kubectl delete namespace pre-release --wait=true || true"
            }
        }
        aborted {
            script {
                echo "Pipeline ABORTED su ${env.BRANCH_NAME}"
                echo "Pulizia risorse..."
                sh "microk8s kubectl delete namespace staging --wait=true || true"
                sh "microk8s kubectl delete namespace pre-release --wait=true || true"
                load "${ORCHESTRATION_DIR}/notificationsFailure.jenkins" //modulo per notifiche email/slack ecc di failure al pusher
            }
        }
    }
}