# Created by nibo at 2015-05-05
Feature: Process Management
  This tests the BPM process control API

  Scenario: Process life management
    Given a new process definition is saved
    And an example process is started
    And the destination peer must receive the command
    And the state must become running
    And the state must become paused
    And the state must become stopped
    And the state must become killed
    And the state must become failed
    And the state must become finished
    And the result must match expectations