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
        // La pulizia 
        stage('Pulizia Workspace Iniziale') {
            steps {
                deleteDir()
                echo "Workspace pulito prima dell'orchestrazione."
            }
        }

        stage('Orchestrator') {
            steps {
                script {
                    // Lista vuota da usare in caso di skip
                    def stepsJump = []
                    
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

                    // *** INIZIO LOGICA DI SKIP INTEGRATA ***

                    def commitMessage = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
                    def stepsToExecute // Variabile che conterrà la lista di step da eseguire
                    
                    if (commitMessage.contains('[skip ci]') || commitMessage.contains('[ci skip]')) {
                        echo "Direttiva [skip ci] trovata. Verranno saltati tutti gli step di orchestrazione."
                        stepsToExecute = stepsJump // Assegna la lista vuota
                    } else {
                        echo "Nessuna direttiva di skip. Esecuzione normale in base al branch."
                        // Logica esistente per la selezione degli step in base al branch
                        if (!(env.BRANCH_NAME in ["develop", "origin/develop", "main", "origin/main", "master", "origin/master"])) {
                            stepsToExecute = stepsFeature
                        } else if (env.BRANCH_NAME in ["develop", "origin/develop"]) {
                            stepsToExecute = stepsDevelop
                        } else if (env.BRANCH_NAME in ["main", "origin/main", "master", "origin/master"]) {
                            stepsToExecute = stepsMaster
                        } else {
                            stepsToExecute = [] // Assicurati che sia vuota se nessuna condizione corrisponde
                        }
                    }

                    // *** FINE LOGICA DI SKIP INTEGRATA ***

                    // Esegue la lista di step che è stata selezionata.
                    // Se è stata selezionata 'stepsJump', questo loop non farà nulla.
                    if (stepsToExecute) { // Controlla che la lista non sia null
                        stepsToExecute.each { fileName ->
                            def filePath = "${ORCHESTRATION_DIR}/${fileName}"
                            echo "Caricando ed eseguendo: ${filePath}"
                            load filePath
                        }
                    }

                    if (!stepsToExecute || stepsToExecute.isEmpty()) {
                        echo "Nessuno step di orchestrazione eseguito."
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
                echo "Pulizia risorse in eccesso..." //ci si assicura che non ci siano risorse residue dopo il deploy o dopo aver compiuto le azioni desiderate
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
