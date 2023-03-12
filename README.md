# Groth16 implementation using Python

This repo contains a basic implementation of `Groth16` protocol in python. 

It uses the [py_ecc](https://github.com/ethereum/py_ecc) library for elliptic curve operations.

If you are just starting out, these are the core files to look into - 

* [Trusted Setup](helpers/dummy_trusted_setup.py)

* [Polynomial Operations](https://github.com/shubham-kanodia/groth-16/blob/main/helpers/polynomial_helper.py)

* [Breaking down simple python program into gates](helpers/snark_helper.py)

* [Prime field operations](fields/field.py)
