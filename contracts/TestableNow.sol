contract TestableNow {

    /* Time override */
	uint _current;


    /** Override current() for testing */
    function current() public returns (uint) {
        return _current;
    }

    function setCurrent(uint __current) {
        _current = __current;
    }

}
