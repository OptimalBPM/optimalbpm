
/**
 * Module that implements a tree using OF, a schema validated form and ui layout

 * @module tokens
 * @service tokens
 * @author Nicklas Börjesson
 * @link https://www.github.com/nicklasb/mbe
 */

export class Part {
    kind: string;
    key: string;
    values: string[];
    match: string[][];
}

export class Verb {
    parts: Part[];
}


export class Translate {

}