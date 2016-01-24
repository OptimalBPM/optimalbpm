
/**
 * Module that implements a tree using MBE, a schema validated form and ui layout

 * @module tokens
 * @service tokens
 * @author Nicklas Börjesson
 * @link https://www.github.com/nicklasb/mbe
 */

export class part {
    kind :string;
    key : string;
    values : string[];
    match  : string[][];
}

export class Verb {
    parts : part[];
}


export class Translate {

}