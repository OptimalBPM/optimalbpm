# Created by nibo at 2015-09-08
Feature: Translation of code to Verb objects and back
  # Enter feature description here

  Scenario: Translate a python source file to a Verb tree
    Given a source file is tokenized
    Then the output must match spot check verbs

  Scenario: Translate an unchanged verb array to JSON and back
    Given a source file is tokenized
    And an array of verb is converted to json
    And it is converted back to verbs
    And is untokenized into another file
    Then the files must match

