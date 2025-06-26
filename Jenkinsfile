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
        // STAGE 1: Preparazione del Workspace e Checkout del Codice
        // Questo stage garantisce che ogni build parta da un ambiente pulito e con il codice corretto.
        stage('Checkout Codice Sorgente') {
            steps {
                // Pulisce il workspace da eventuali residui di build precedenti.
                // 'cleanWs()' è preferibile a 'deleteDir()' perché più integrato e sicuro.
                cleanWs()

                // Esegue il checkout del codice sorgente. 'scm' è una variabile globale in un
                // Multibranch Pipeline che si riferisce alla configurazione Git del branch corrente.
                checkout scm
                
                echo "Workspace pulito e checkout completato per il branch: ${env.BRANCH_NAME}"
            }
        }

        // STAGE 2: Esecuzione della logica di orchestrazione
        // Questo stage viene eseguito solo dopo che il workspace è stato preparato correttamente.
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
                    
                    // Questo comando ora funzionerà perché il workspace contiene il repository .git
                    def commitMessage = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
                    def stepsToExecute = [] // Inizializza sempre a una lista vuota per sicurezza
                    
                    if (commitMessage.contains('[skip ci]') || commitMessage.contains('[ci skip]')) {
                        echo "Direttiva [skip ci] trovata. Verranno saltati tutti gli step di orchestrazione."
                        // stepsToExecute rimane vuota
                    } else {
                        echo "Nessuna direttiva di skip. Esecuzione normale in base al branch: '${env.BRANCH_NAME}'"
                        
                        // Logica di selezione branch migliorata e più robusta
                        if (env.BRANCH_NAME == 'develop' || env.BRANCH_NAME == 'origin/develop') {
                            echo "Branch 'develop' rilevato. Esecuzione degli step di CD-Develop."
                            stepsToExecute = stepsDevelop
                        } else if (env.BRANCH_NAME == 'main' || env.BRANCH_NAME == 'master' || env.BRANCH_NAME == 'origin/main' || env.BRANCH_NAME == 'origin/master') {
                            echo "Branch 'main' o 'master' rilevato. Esecuzione degli step di CD-Master."
                            stepsToExecute = stepsMaster
                        } else {
                            // Qualsiasi altro branch viene considerato un feature branch.
                            echo "Rilevato un feature branch (o un altro branch non principale). Esecuzione degli step di CI-Feature."
                            stepsToExecute = stepsFeature
                        }
                    }

                    // *** FINE LOGICA DI SKIP INTEGRATA ***

                    // Esegue la lista di step che è stata selezionata.
                    // Se la lista è vuota, questo loop non farà nulla.
                    if (stepsToExecute) { 
                        stepsToExecute.each { fileName ->
                            def filePath = "${ORCHESTRATION_DIR}/${fileName}"
                            echo "Caricando ed eseguendo: ${filePath}"
                            load filePath
                        }
                    }

                    if (stepsToExecute.isEmpty()) {
                        echo "Nessuno step di orchestrazione è stato eseguito."
                    }
                }
            }
        }
    }

    post {
        failure {
            script {
                echo "Pipeline fallita su ${env.BRANCH_NAME}"
                
                // Aggiungiamo un checkout qui per essere sicuri di avere lo script di notifica
                // anche se la pipeline fallisce prima di averlo caricato.
                try {
                    checkout scm
                    load "${ORCHESTRATION_DIR}/notificationsFailure.jenkins" //modulo per notifiche email/slack ecc di failure al pusher
                } catch (Exception e) {
                    echo "Impossibile caricare lo script di notifica: ${e.message}"
                }
                
                echo "Pulizia risorse..."
                sh "microk8s kubectl delete namespace staging --ignore-not-found=true --wait=true || true"
                sh "microk8s kubectl delete namespace pre-release --ignore-not-found=true --wait=true || true"
            }
        }
        success {
            script {
                echo "Pipeline completata con successo su ${env.BRANCH_NAME}"
                echo "Pulizia risorse in eccesso..." //ci si assicura che non ci siano risorse residue dopo il deploy o dopo aver compiuto le azioni desiderate
                sh "microk8s kubectl delete namespace staging --ignore-not-found=true --wait=true || true"
                sh "microk8s kubectl delete namespace pre-release --ignore-not-found=true --wait=true || true"
            }
        }
        aborted {
            script {
                echo "Pipeline ABORTED su ${env.BRANCH_NAME}"
                // Aggiungiamo un checkout qui per lo stesso motivo del blocco 'failure'
                 try {
                    checkout scm
                    load "${ORCHESTRATION_DIR}/notificationsFailure.jenkins" //modulo per notifiche email/slack ecc di failure al pusher
                } catch (Exception e) {
                    echo "Impossibile caricare lo script di notifica: ${e.message}"
                }
                
                echo "Pulizia risorse..."
                sh "microk8s kubectl delete namespace staging --ignore-not-found=true --wait=true || true"
                sh "microk8s kubectl delete namespace pre-release --ignore-not-found=true --wait=true || true"
            }
        }
    }
}