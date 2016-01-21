# Created by nibo at 2015-05-19
Feature: Handle in- and outgoing messages
  The agent must be able to handle messaging

  Scenario: A worker process sends a message
    Given a process mockup puts a message on the send_queue
    Then it should reach the broker mockup
    And a response should be sent
    And be received by the worker handler

  Scenario: A agent receives a process start message and there is an error
    Given a broker mockup sends a process start message
    Then a control mockup should receive the message
    And the broker mockup should receive an error message

