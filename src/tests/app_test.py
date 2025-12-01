import unittest
from app import app, warehouses


class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        warehouses.clear()

    def tearDown(self):
        warehouses.clear()

    def test_index_empty(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Varastot', response.data)

    def test_create_warehouse_get(self):
        response = self.app.get('/warehouse/create')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Luo uusi varasto', response.data)

    def test_create_warehouse_post(self):
        response = self.app.post('/warehouse/create', data={
            'name': 'Test Warehouse',
            'capacity': '100',
            'initial_balance': '10'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Warehouse', response.data)
        self.assertEqual(len(warehouses), 1)

    def test_create_warehouse_empty_name(self):
        response = self.app.post('/warehouse/create', data={
            'name': '',
            'capacity': '100',
            'initial_balance': '0'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Nimi on pakollinen'.encode('utf-8'), response.data)

    def test_create_warehouse_invalid_capacity(self):
        response = self.app.post('/warehouse/create', data={
            'name': 'Test',
            'capacity': '-10',
            'initial_balance': '0'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Tilavuuden on oltava positiivinen'.encode('utf-8'),
            response.data
        )

    def test_view_warehouse(self):
        self.app.post('/warehouse/create', data={
            'name': 'View Test',
            'capacity': '50',
            'initial_balance': '20'
        })
        response = self.app.get('/warehouse/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'View Test', response.data)

    def test_view_nonexistent_warehouse(self):
        response = self.app.get('/warehouse/999', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Varastoa ei löytynyt'.encode('utf-8'),
            response.data
        )

    def test_edit_warehouse(self):
        self.app.post('/warehouse/create', data={
            'name': 'Original Name',
            'capacity': '100',
            'initial_balance': '0'
        })
        response = self.app.post('/warehouse/1/edit', data={
            'name': 'New Name',
            'capacity': '200'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New Name', response.data)

    def test_delete_warehouse(self):
        self.app.post('/warehouse/create', data={
            'name': 'Delete Me',
            'capacity': '100',
            'initial_balance': '0'
        })
        self.assertEqual(len(warehouses), 1)
        response = self.app.post(
            '/warehouse/1/delete',
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(warehouses), 0)

    def test_add_to_warehouse(self):
        self.app.post('/warehouse/create', data={
            'name': 'Add Test',
            'capacity': '100',
            'initial_balance': '0'
        })
        response = self.app.post('/warehouse/1/add', data={
            'amount': '50'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(warehouses[1]['varasto'].saldo, 50)

    def test_add_exceeds_capacity(self):
        self.app.post('/warehouse/create', data={
            'name': 'Capacity Test',
            'capacity': '50',
            'initial_balance': '40'
        })
        response = self.app.post('/warehouse/1/add', data={
            'amount': '20'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Ei tarpeeksi tilaa'.encode('utf-8'), response.data)

    def test_remove_from_warehouse(self):
        self.app.post('/warehouse/create', data={
            'name': 'Remove Test',
            'capacity': '100',
            'initial_balance': '50'
        })
        response = self.app.post('/warehouse/1/remove', data={
            'amount': '30'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(warehouses[1]['varasto'].saldo, 20)

    def test_remove_exceeds_balance(self):
        self.app.post('/warehouse/create', data={
            'name': 'Balance Test',
            'capacity': '100',
            'initial_balance': '20'
        })
        response = self.app.post('/warehouse/1/remove', data={
            'amount': '50'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Ei tarpeeksi tavaraa'.encode('utf-8'), response.data)
