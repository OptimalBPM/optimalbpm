# Created by nibo at 2015-05-18
Feature: Worker process functionality
  # Enter feature description here
  Scenario: A BPM process is run and a worker is reused
    Given a process start message is sent to control monitor
    Then a worker process instance message should be received by broker socket
    And a bpm process instance message should be received by broker socket
    And a process running state message should be received by broker socket
    And a log message from the process should be received by the broker socket
    And a process result message from the process should be received by the broker socket
    And a second process start message is sent to the control monitor
    And a log message from the second process should be received by the broker socket
    And a third process start message is sent to the control monitor
    And a third process result message should be received by the broker socket
    And a process stop message should be sent to the second process
    And a second process running state stopped message should be received by the socket


  Scenario: A running BPM process has to be killed
    Given a blocking process start message is sent to control monitor
    Then a process progress message should be received by broker socket
    And the broker should send a process stop message to the worker
    And the broker should not receive a success message
    And the broker should send a process kill message to the worker
    And the broker should receive a process state killed message

