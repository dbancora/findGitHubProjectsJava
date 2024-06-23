# 🔎 Find GitHub Projects 

Gli script in Python presenti in repository, hanno lo scopo di cercare all'interno del sito _github_ le repository che utilizzano il framework JUnit.
Attualmente, gli script sono in grado di estrarre il metodo con annotazione @Test (presenti nelle classi Java) e cercare, seppur in modo parziale, il metodo focale che viene richiamato all'interno degli _assert_.
Lo scopo del programma è quello di generare un dataset che contiene i metodi di test (e i rispettivi metodi focali). 


# Descrizione del Workflow del Programma

## ▶️ Ricerca delle repository candidate
Il programma inizia eseguendo la funzione principale all'interno del blocco `if __name__ == '__main__':`.
che accetta come parametro l'anno di ricerca delle repository utile per formulare le query di ricerca su GitHub.

### Ricerca delle repository tramite github.repository
La query template per cercare repository Java sfrutta le API di github e potrebbe comprendere i seguenti parametri di ricerca:
   
   - **Linguaggio**: Java;
   - **Numero di star**: >25;  
   - **Ultimo commmit pushato**: >2020-01-01.

`language:Java stars:>25 pushed:>2020-01-01`

Per eseguire questa prima ricerca, è necessario rispettare i limiti imposti dalle API di Github che comprendono:
   
   1. Massimo _30_ richieste per minuto;
   2. Massimo _1000_ repository visualizzabili dalla singola ricerca; 

Al fine di superare queste limitazioni, è necessario inserire un `time.sleep(2)` tra una ricerca e la successiva ed
aggiungere un campo alla query di ricerca che verifica la data di creazione della repository. 

La nuova query sarà quindi la seguente: 

`language:Java stars:>25 pushed:>2020-01-01 created:{}-{:02d}-{:02d}..{}-{:02d}-{:02d}`

In questo modo è possibile recuperare tutte le repository che sono state create in un intervallo specifico. Anche in questo caso, per superare
la limitazione _2_ (Massimo 100 repository visualizzabili per ricerca) è possibile suddividere il mese in blocchi da 10 giorni: 
di conseguenza, verranno eseguite 3 query per ogni mese e le repository trovate verranno salvate in una lista. 

### Ricerca delle repository tramite github.code

Un ulteriore query possibile comprende la ricerca tramite le API di `github.code`ed in particolare è possibile visualizzare se all'interno del codice
è presente un import a **JUnit** tramite la query: 

`"import org.junit"` 

Questa ulteriore ricerca consente di andare a visualizzare tutte le repository che utilizzano JUnit come dipendenza all'interno dei file
e di conseguenza contengono dei metodi con annotazione _@Test_. 

Purtroppo, se si utilizzano le API `github.code` non è possibile verificare direttamente la data di creazione delle repository stesse e
di conseguenza è necessario salvare il nome e il link della repository, per poi verificare successivamente la data di creazione, le ultime modifiche e le star 
della repository in questione. 

## ▶️ Filtraggio delle repository 
Una volta eseguiti i passaggi sopra descritti, è possibile scremare le reposiotry trovate seguendo i seguenti passaggi:
   1. **_Verificare che non ci siano repository duplicate_:**  a causa delle due diverse api utilizzate nei passaggi precedenti, potrebbe accadere che
   una repoitory sia contenuta sia nella lista che contiene i progetti selezionati tramite `github.repsitory` e sia con `github.code`. 
   E' necessario quindi procedere tramite verifica incrociata per verificare l'unicità della repository all'interno delle due liste.
   2. **_Verificare che le repository contengano i file pom.xml e la dipendenza JUnit_**: per garantire che tutte le repository contengano all'interno dei metodi che abbiano come
      annotazione _@Test_ è necessario verificare che sia presente sia il file pom.xml, sia la dipendenza JUnit, così da garantire una maggiore probabilità della presenza di classi di Test.
   3. **_Salvataggio delle nuove repository all'interno di un file Json_**: una volta terminato il primo filtraggio delle repository, è necessario salvare il nome della repository e il suo link
   all'interno di un file Json, così che possa essere elaborato nei passaggi successivi. 

Tutte le repository che non soddisfano i requisiti sopra specificati è possibile scartarle, in quanto non constituiscono elemento utile per la creazione del dataset. 

## ▶️ Ricerca del metodo di test e del metodo focale
Eseguito il filtraggio delle repository, è necessario ora ricercare i _metodi di test_ che utiizzano JUnit. Per fare cioò e necessario seguire i seguenti passaggi:

- _**Scaricare la repository**_
- _**Ricerca dei metodi con annotazione @Test**_: i metodi di test, in JUnit, sono preceduti dall'annotazione _@Test_. Di conseguenza, è necessario ricercare nel codice questi metodi, salvare il loro nome e il loro corpo.
Una volta eseguita questa ricerca è possibile verificare se il nome della classe che contiene i test è del tipo "_Test[nome della classe da testare]_": se così fosse, presumibilmente, la classe contentente i test verifica il corretto funzionamento
dei metodi contenuti all'interno di _[nome della classe da testare]_. 
Di conseguenza, è possibile salvare il nome della classe, così da procedere successivamente alla ricerca del metodo focale all'interno di quella classe. 
- _**Ricerca del metodo focale**_: dopo avere trovato i metodi di test, è necessario analizzare il corpo del metodo per ricercare _l'assert_. Una volta trovato l'assert, è necessario analizzare i parametri che vengono passati per cercare di individuare il metodo focale che viene testato:
  1. Se il nome della classe che contiene i Test JUnit è del tipo "_Test[nome della classe da testare]_" allora, presumibilmente, i metodi contenuti all'interno dell'_assert_ sono contenuti all'interno della classe _[nome della classe da testare]_ quindi, una volta estratto il metodo focale, 
  è necessario cercare il nome del metodo focale all'interno di quella classe. 
  2. Se la condizione (i) non è verificata allora, una volta estratto il metodo focale dall'_assert_, è necessario ricercare il candidato metodo focale all'interno del codice sorgente: 
     - Nel caso in cui non venga trovato alcun metodo che corrisponde al candidato metodo focale, allora si potrebbe scartare la repository. 
     - Se invece il candidato metodo focale trova corrispondenza all'interno di una classe della repository, allora è necessario salvare la definizione del metodo in un file Json.
- _**Casi particolari per la ricerca del metodo focale**_: nel caso in cui non sia possibile trovare il metodo focale con le metodologie descritte nel punto precedente, è necessario procedere con alcune considerazioni:
  1. Se si trovano più definizioni del metodo focale all'interno del codice della repository, è necessario analizzare nuovamente l'_assert_ e verificare su quale classe il metodo focale viene chiamato. In questo modo è possibile ricercare all'interno di una classe specifica del programma il metodo, salvarlo e riportarlo all'interno del file JSon. Nel caso in cui non fosse possibile trovare il metodo focale, allora la repository dovrebbe essere scartata. 
  2. Nel caso in cui all'interno dell'_assert_ non venga invocato alcun metdo, ma si verificano esclusivamente dei confronti tra variabili, allora è necessario eseguire un'analisi più approfondita per analizzare il corpo del metodo di test, così  da capire quale sia il metodo focale che viene invocato. Generalmente, si potrebbe pensare di analizzare la riga che precede l'_assert_
  così da verificare se viene invocato un metodo che potrebbe corrispondere al metodo focale. Nel caso in cui non vi sia alcun metodo invocato, allora la repository viene scartata e si passa all'analisi della successiva.

## ▶️ Creazione del file Json contente i risultati 
Una volta che il metodo di test ed il metodo focale sono stati individuati all'interno del programma, è necessario salvarli entrambi in un file JSon che contiene sia il corpo del metodo di test, sia il corpo del metodo focale.
Terminata la ricerca, è possibile poi eliminare la repository scaricata e passare alla successiva. 