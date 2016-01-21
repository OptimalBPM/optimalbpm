# Created by nibo at 2016-01-21
Feature: Optimal BPM startup and shutdown scenarios
  These scenarios will cover different startup- and shutdown scenarios


  Scenario: Starting broker and an agent and terminate and restart the broker
    Given the broker is started
    And we wait 1 seconds
    And it is it possible to register an agent at the broker
    And the agent is started
    And we wait 1 seconds
    And the agent process is registered
    And the broker is told to restart using the API
    And we wait 5 seconds
    And there is a web_socket peer with the address agent01
    And the agent is told to stop using the API
    And we wait 2 seconds
    And the broker is told to stop using the API
    And we wait 2 seconds
    And a get environment request should fail

  Scenario: Starting broker and an several agents
    # Enter steps here