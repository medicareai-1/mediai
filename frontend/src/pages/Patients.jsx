import { useState, useEffect } from 'react';
import { collection, query, onSnapshot, addDoc } from 'firebase/firestore';
import { db } from '../services/firebase';
import { useAuth } from '../contexts/AuthContext';
import { Users, Plus, Search, User, Mail, Phone, Calendar } from 'lucide-react';

function Patients() {
  const { currentUser } = useAuth();
  const [patients, setPatients] = useState([]);
  const [filteredPatients, setFilteredPatients] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [newPatient, setNewPatient] = useState({
    name: '',
    age: '',
    gender: 'male',
    contact: '',
    email: '',
    medical_history: ''
  });

  useEffect(() => {
    // Real-time listener for patients
    const patientsQuery = query(collection(db, 'patients'));

    const unsubscribe = onSnapshot(patientsQuery, (snapshot) => {
      const patientsList = [];
      snapshot.forEach((doc) => {
        patientsList.push({ id: doc.id, ...doc.data() });
      });
      setPatients(patientsList);
      setFilteredPatients(patientsList);
      setLoading(false);
    }, (error) => {
      console.error('Error fetching patients:', error);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  useEffect(() => {
    // Filter patients based on search
    const filtered = patients.filter(patient =>
      patient.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      patient.contact?.includes(searchTerm) ||
      patient.email?.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredPatients(filtered);
  }, [searchTerm, patients]);

  const handleAddPatient = async (e) => {
    e.preventDefault();

    try {
      await addDoc(collection(db, 'patients'), {
        ...newPatient,
        age: parseInt(newPatient.age),
        created_at: new Date().toISOString(),
        user_id: currentUser.uid
      });

      // Reset form
      setNewPatient({
        name: '',
        age: '',
        gender: 'male',
        contact: '',
        email: '',
        medical_history: ''
      });
      setShowAddModal(false);
    } catch (error) {
      console.error('Error adding patient:', error);
      alert('Failed to add patient');
    }
  };

  const PatientCard = ({ patient }) => (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 hover:shadow-xl transition-all transform hover:scale-105">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-4">
          <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-md">
            <User className="w-7 h-7 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">{patient.name}</h3>
            <p className="text-sm text-gray-500 font-medium">
              👤 {patient.age} years • {patient.gender}
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {patient.contact && (
          <div className="flex items-center text-sm text-gray-700 bg-blue-50 px-3 py-2 rounded-lg">
            <Phone className="w-4 h-4 mr-2 text-blue-600" />
            <span className="font-medium">{patient.contact}</span>
          </div>
        )}
        {patient.email && (
          <div className="flex items-center text-sm text-gray-700 bg-green-50 px-3 py-2 rounded-lg">
            <Mail className="w-4 h-4 mr-2 text-green-600" />
            <span className="font-medium">{patient.email}</span>
          </div>
        )}
        {patient.created_at && (
          <div className="flex items-center text-sm text-gray-700 bg-purple-50 px-3 py-2 rounded-lg">
            <Calendar className="w-4 h-4 mr-2 text-purple-600" />
            <span className="font-medium">Registered: {new Date(patient.created_at).toLocaleDateString()}</span>
          </div>
        )}
      </div>

      {patient.medical_history && (
        <div className="mt-4 pt-4 border-t-2 border-gray-100">
          <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">
            <span className="font-semibold text-gray-900">📋 Medical History: </span>
            {patient.medical_history}
          </p>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header with gradient */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-8 text-white shadow-xl">
        <div className="flex justify-between items-center">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-white bg-opacity-20 rounded-lg backdrop-blur-sm">
                <Users className="w-6 h-6" />
              </div>
              <h1 className="text-4xl font-bold">👥 Patient Management</h1>
            </div>
            <p className="text-blue-100 text-lg">Manage patient records and information</p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center px-6 py-3 bg-white text-blue-600 font-semibold rounded-xl hover:bg-blue-50 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <Plus className="w-5 h-5 mr-2" />
            Add Patient
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="🔍 Search by name, contact, or email..."
            className="w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 hover:bg-white text-lg"
          />
        </div>
      </div>

      {/* Patients Grid */}
      {loading ? (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-16 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto"></div>
          <p className="mt-6 text-gray-600 font-medium text-lg">Loading patients...</p>
        </div>
      ) : filteredPatients.length === 0 ? (
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl shadow-lg border-2 border-dashed border-gray-300 p-16 text-center">
          <Users className="w-20 h-20 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-900 mb-2">No patients found</h3>
          <p className="text-gray-600 text-lg">
            {searchTerm ? 'Try a different search term' : 'Add your first patient to get started'}
          </p>
          {!searchTerm && (
            <button
              onClick={() => setShowAddModal(true)}
              className="mt-6 inline-flex items-center px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-all shadow-lg"
            >
              <Plus className="w-5 h-5 mr-2" />
              Add First Patient
            </button>
          )}
        </div>
      ) : (
        <div>
          <div className="mb-4 text-sm text-gray-600 font-medium">
            Showing {filteredPatients.length} of {patients.length} patient(s)
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredPatients.map((patient) => (
              <PatientCard key={patient.id} patient={patient} />
            ))}
          </div>
        </div>
      )}

      {/* Add Patient Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 transform transition-all">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Plus className="w-6 h-6 text-blue-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Add New Patient</h2>
            </div>

            <form onSubmit={handleAddPatient} className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Full Name *
                </label>
                <input
                  type="text"
                  required
                  value={newPatient.name}
                  onChange={(e) => setNewPatient({ ...newPatient, name: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 hover:bg-white"
                  placeholder="John Doe"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Age *
                  </label>
                  <input
                    type="number"
                    required
                    value={newPatient.age}
                    onChange={(e) => setNewPatient({ ...newPatient, age: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 hover:bg-white"
                    placeholder="25"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Gender *
                  </label>
                  <select
                    value={newPatient.gender}
                    onChange={(e) => setNewPatient({ ...newPatient, gender: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 hover:bg-white"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  📞 Contact Number
                </label>
                <input
                  type="tel"
                  value={newPatient.contact}
                  onChange={(e) => setNewPatient({ ...newPatient, contact: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 hover:bg-white"
                  placeholder="+1 234 567 8900"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  📧 Email
                </label>
                <input
                  type="email"
                  value={newPatient.email}
                  onChange={(e) => setNewPatient({ ...newPatient, email: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 hover:bg-white"
                  placeholder="john@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  📋 Medical History
                </label>
                <textarea
                  value={newPatient.medical_history}
                  onChange={(e) => setNewPatient({ ...newPatient, medical_history: e.target.value })}
                  rows="3"
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 hover:bg-white resize-none"
                  placeholder="Previous conditions, allergies, etc."
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  Add Patient
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-6 py-3 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-all font-semibold hover:border-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Patients;

